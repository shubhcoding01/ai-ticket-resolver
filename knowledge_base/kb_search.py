import os
import re
import logging
from datetime   import datetime
from dotenv     import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

CHROMA_DIR      = os.getenv("KB_CHROMA_DIR",       "knowledge_base/chroma_db")
COLLECTION_NAME = os.getenv("KB_COLLECTION_NAME",  "it_support_kb")
MAX_RESULTS     = int(os.getenv("KB_MAX_RESULTS",  3))
MIN_SCORE       = float(os.getenv("KB_MIN_SCORE",  0.3))
EMBED_MODEL     = os.getenv("KB_EMBED_MODEL",      "all-MiniLM-L6-v2")

_chroma_client     = None
_collection        = None
_embedding_function = None


def _get_collection():
    """
    Get or initialize the ChromaDB collection.
    Uses module-level singleton so connection is
    created once and reused across all search calls.
    Lazy initialization — only connects when first search
    is made, not at import time.

    Returns:
        ChromaDB collection object or None if unavailable
    """
    global _chroma_client, _collection, _embedding_function

    if _collection is not None:
        return _collection

    try:
        import chromadb
        from chromadb.utils import embedding_functions

        if not os.path.exists(CHROMA_DIR):
            log.warning(
                f"ChromaDB directory not found: '{CHROMA_DIR}'. "
                "Run kb_indexer.py first to build the index."
            )
            return None

        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

        _embedding_function = (
            embedding_functions
            .SentenceTransformerEmbeddingFunction(
                model_name=EMBED_MODEL
            )
        )

        try:
            _collection = _chroma_client.get_collection(
                name               = COLLECTION_NAME,
                embedding_function = _embedding_function,
            )
            log.info(
                f"Connected to KB collection '{COLLECTION_NAME}' "
                f"with {_collection.count()} chunk(s)."
            )
            return _collection

        except Exception:
            log.warning(
                f"KB collection '{COLLECTION_NAME}' not found. "
                "Run kb_indexer.py first to build the index."
            )
            return None

    except ImportError:
        log.error(
            "chromadb not installed. Run:\n"
            "  pip install chromadb sentence-transformers"
        )
        return None

    except Exception as e:
        log.error(f"Failed to connect to ChromaDB: {e}")
        return None


def search_knowledge_base(
    query      : str,
    max_results: int   = None,
    min_score  : float = None,
) -> str | None:
    """
    Main search function called by orchestrator.py.
    Searches the ChromaDB vector store for the most
    relevant IT support guide content matching the query.

    This is the only function orchestrator.py needs to call.
    Returns clean formatted text ready to send to the user,
    or None if no relevant content is found.

    Args:
        query       : Ticket description or search query text
        max_results : Max number of chunks to retrieve
                      (defaults to KB_MAX_RESULTS from .env)
        min_score   : Minimum relevance score 0.0 to 1.0
                      (defaults to KB_MIN_SCORE from .env)

    Returns:
        Formatted guide text string ready to send to user,
        or None if no relevant guide found above threshold
    """
    if not query or not query.strip():
        log.warning("search_knowledge_base called with empty query.")
        return None

    max_results = max_results or MAX_RESULTS
    min_score   = min_score   or MIN_SCORE

    log.info(f"KB search query: '{query[:80]}...'")

    cleaned_query = _clean_query(query)
    results       = _vector_search(cleaned_query, max_results)

    if not results:
        log.info("No results from vector search.")
        return None

    filtered = _filter_by_score(results, min_score)

    if not filtered:
        log.info(
            f"No results above minimum score threshold "
            f"({min_score}). Best score was "
            f"{results[0]['score']:.3f}."
        )
        return None

    deduplicated = _deduplicate_results(filtered)
    formatted    = _format_guide(deduplicated, query)

    log.info(
        f"KB search returned {len(deduplicated)} relevant "
        f"chunk(s) for query."
    )

    return formatted


def search_with_details(
    query      : str,
    max_results: int   = None,
    min_score  : float = None,
) -> list:
    """
    Extended search that returns full result details
    including scores, source files, and chunk metadata.
    Useful for debugging search quality and for the
    Streamlit dashboard search explorer.

    Args:
        query       : Search query text
        max_results : Max chunks to retrieve
        min_score   : Minimum relevance score

    Returns:
        List of result dicts with keys:
            text, score, file_name, chunk_index,
            word_count, indexed_at, rank
    """
    if not query or not query.strip():
        return []

    max_results = max_results or MAX_RESULTS
    min_score   = min_score   or MIN_SCORE

    cleaned_query = _clean_query(query)
    results       = _vector_search(cleaned_query, max_results * 2)

    if not results:
        return []

    filtered     = _filter_by_score(results, min_score)
    deduplicated = _deduplicate_results(filtered)

    for rank, result in enumerate(deduplicated, start=1):
        result["rank"] = rank

    return deduplicated


def search_by_category(category: str) -> str | None:
    """
    Search the knowledge base using a ticket category name
    rather than the full ticket description.
    Useful as a fallback when the description is very short.

    Args:
        category : Ticket category string from ai_classifier.py
                   e.g. 'antivirus', 'vpn', 'password_reset'

    Returns:
        Formatted guide text or None if not found
    """
    category_queries = {
        "app_install"       : "how to install software application on Windows laptop",
        "antivirus"         : "antivirus not working virus definitions update scan",
        "password_reset"    : "forgot password account locked reset windows login",
        "network"           : "cannot connect to internet VPN network not working",
        "printer"           : "printer offline not printing print queue stuck",
        "email_issue"       : "outlook not working email not sending receiving pst",
        "hardware"          : "laptop hardware issue screen keyboard battery",
        "os_issue"          : "windows update failed blue screen system crash slow",
        "access_permission" : "access denied folder permission shared drive",
        "other"             : "IT support help troubleshooting",
    }

    query = category_queries.get(category, category)
    log.info(f"Category search for '{category}' using query: '{query}'")
    return search_knowledge_base(query)


def search_multi_query(queries: list) -> str | None:
    """
    Run multiple search queries and merge the best results.
    Useful when a ticket covers multiple issues.
    For example a ticket about both VPN and Outlook issues
    will get guides for both topics merged into one response.

    Args:
        queries : List of query strings to search

    Returns:
        Merged formatted guide text or None
    """
    if not queries:
        return None

    all_results = []
    seen_ids    = set()

    for query in queries:
        if not query.strip():
            continue

        cleaned = _clean_query(query)
        results = _vector_search(cleaned, MAX_RESULTS)

        for result in results:
            chunk_id = result.get("id", "")
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                all_results.append(result)

    if not all_results:
        return None

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    filtered     = _filter_by_score(all_results, MIN_SCORE)
    deduplicated = _deduplicate_results(filtered)

    if not deduplicated:
        return None

    return _format_guide(deduplicated, " | ".join(queries))


def is_kb_available() -> bool:
    """
    Check if the knowledge base index is built and ready.
    Called by orchestrator.py before attempting a search.

    Returns:
        True if ChromaDB collection exists and has documents
    """
    try:
        collection = _get_collection()
        if collection is None:
            return False
        count = collection.count()
        return count > 0

    except Exception as e:
        log.error(f"KB availability check failed: {e}")
        return False


def get_kb_stats() -> dict:
    """
    Return statistics about the knowledge base.
    Used by the Streamlit dashboard to show KB status.

    Returns:
        Dict with total_chunks, collection_name,
        is_available, chroma_dir
    """
    try:
        collection = _get_collection()

        if collection is None:
            return {
                "is_available"    : False,
                "total_chunks"    : 0,
                "collection_name" : COLLECTION_NAME,
                "chroma_dir"      : CHROMA_DIR,
                "embed_model"     : EMBED_MODEL,
            }

        return {
            "is_available"    : True,
            "total_chunks"    : collection.count(),
            "collection_name" : COLLECTION_NAME,
            "chroma_dir"      : CHROMA_DIR,
            "embed_model"     : EMBED_MODEL,
        }

    except Exception as e:
        log.error(f"Cannot get KB stats: {e}")
        return {
            "is_available" : False,
            "error"        : str(e),
        }


def _vector_search(query: str, n_results: int) -> list:
    """
    Execute a vector similarity search against ChromaDB.
    Returns raw results with cosine similarity scores.

    ChromaDB returns distances not similarities — we convert
    distance to a similarity score where 1.0 = perfect match
    and 0.0 = completely unrelated.

    Args:
        query     : Cleaned search query text
        n_results : Number of results to retrieve

    Returns:
        List of result dicts with text, score, metadata, id
        Sorted by score descending (best match first)
    """
    collection = _get_collection()

    if collection is None:
        log.warning("KB collection unavailable — cannot search.")
        return []

    if collection.count() == 0:
        log.warning("KB collection is empty — run kb_indexer.py first.")
        return []

    try:
        n_results = min(n_results, collection.count())

        raw = collection.query(
            query_texts = [query],
            n_results   = n_results,
            include     = ["documents", "metadatas", "distances"],
        )

        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]
        ids       = raw.get("ids",       [[]])[0]

        results = []

        for doc, meta, dist, chunk_id in zip(
            documents, metadatas, distances, ids
        ):
            similarity = max(0.0, 1.0 - dist)

            results.append({
                "text"        : doc,
                "score"       : round(similarity, 4),
                "file_name"   : meta.get("file_name",   "unknown"),
                "chunk_index" : meta.get("chunk_index", 0),
                "word_count"  : meta.get("word_count",  0),
                "indexed_at"  : meta.get("indexed_at",  ""),
                "id"          : chunk_id,
            })

        results.sort(key=lambda x: x["score"], reverse=True)

        log.debug(
            f"Vector search returned {len(results)} result(s). "
            f"Top score: {results[0]['score']:.3f}"
            if results else
            "Vector search returned 0 results."
        )

        return results

    except Exception as e:
        log.error(f"ChromaDB query failed: {e}")
        return []


def _filter_by_score(results: list, min_score: float) -> list:
    """
    Remove results below the minimum relevance threshold.

    Args:
        results   : List of result dicts from _vector_search()
        min_score : Minimum score to keep (0.0 to 1.0)

    Returns:
        Filtered list of result dicts
    """
    filtered = [r for r in results if r["score"] >= min_score]

    log.debug(
        f"Score filter ({min_score}): "
        f"{len(results)} → {len(filtered)} results."
    )

    return filtered


def _deduplicate_results(results: list) -> list:
    """
    Remove duplicate or near-duplicate chunks from results.
    ChromaDB may return multiple chunks from the same section
    of a document — this keeps only the best one per source file
    unless the chunks cover clearly different topics.

    Deduplication strategy:
        1. Keep max 2 chunks per source file
        2. If two chunks share more than 60% of their words
           keep only the higher-scoring one

    Args:
        results : List of result dicts from _filter_by_score()

    Returns:
        Deduplicated list of result dicts
    """
    if not results:
        return []

    file_counts = {}
    deduplicated = []

    for result in results:
        file_name = result["file_name"]
        count     = file_counts.get(file_name, 0)

        if count >= 2:
            log.debug(
                f"Skipping extra chunk from '{file_name}' "
                f"(already have {count})."
            )
            continue

        is_duplicate = False
        for existing in deduplicated:
            overlap = _text_overlap_ratio(
                result["text"],
                existing["text"]
            )
            if overlap > 0.6:
                log.debug(
                    f"Skipping near-duplicate chunk "
                    f"(overlap ratio: {overlap:.2f})."
                )
                is_duplicate = True
                break

        if not is_duplicate:
            deduplicated.append(result)
            file_counts[file_name] = count + 1

    log.debug(
        f"Deduplication: "
        f"{len(results)} → {len(deduplicated)} results."
    )

    return deduplicated


def _text_overlap_ratio(text_a: str, text_b: str) -> float:
    """
    Calculate what fraction of words in text_a also
    appear in text_b. Used for near-duplicate detection.

    Args:
        text_a : First text string
        text_b : Second text string

    Returns:
        Overlap ratio between 0.0 and 1.0
    """
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())

    if not words_a:
        return 0.0

    intersection = words_a & words_b
    return len(intersection) / len(words_a)


def _clean_query(query: str) -> str:
    """
    Clean and normalize the query text before searching.
    Removes noise words and special characters that hurt
    vector search quality.

    Steps:
        1. Lowercase and strip whitespace
        2. Expand common IT contractions
        3. Remove email addresses and machine names
           (these confuse the embedding model)
        4. Remove excessive punctuation
        5. Trim to max 200 words
           (very long queries hurt embedding quality)

    Args:
        query : Raw query text from ticket description

    Returns:
        Cleaned query string
    """
    if not query:
        return ""

    text = query.lower().strip()

    it_expansions = {
        "av"    : "antivirus",
        "pw"    : "password",
        "pwd"   : "password",
        "os"    : "operating system",
        "o365"  : "office 365",
        "ms"    : "microsoft",
        "pc"    : "computer",
        "vpn"   : "virtual private network vpn",
        "mfa"   : "multi factor authentication mfa",
        "otp"   : "one time password otp",
        "pst"   : "outlook pst email file",
        "bsod"  : "blue screen of death error",
        "rdp"   : "remote desktop rdp",
        "asap"  : "",
        "fyi"   : "",
        "pls"   : "please",
        "plz"   : "please",
        "thx"   : "",
        "thnks" : "",
        "plzz"  : "please",
    }

    words = text.split()
    words = [
        it_expansions.get(w, w)
        for w in words
    ]
    text = " ".join(words)

    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '',
        text
    )

    text = re.sub(
        r'\b[A-Z]{2,6}[-_]?[A-Z0-9]{0,4}[-_]?\d{3,6}\b',
        '',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r'\b\d{3,}\b', '', text)

    text = re.sub(r'[^\w\s\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    words = text.split()
    if len(words) > 200:
        text = " ".join(words[:200])
        log.debug(f"Query trimmed to 200 words.")

    log.debug(f"Cleaned query: '{text[:100]}...'")
    return text


def _format_guide(results: list, original_query: str) -> str:
    """
    Format the search results into a clean, readable
    self-help guide ready to send to the user via email
    or Freshdesk public reply.

    Formatting strategy:
        - If results are from one file: format as a single guide
        - If results are from multiple files: format each
          source as a separate section with a header
        - Add a header describing what the guide covers
        - Highlight key steps with numbered formatting
        - Add a footer asking user to confirm if guide helped

    Args:
        results        : List of deduplicated result dicts
        original_query : The original search query for context

    Returns:
        Formatted guide string
    """
    if not results:
        return ""

    source_files = list({r["file_name"] for r in results})
    timestamp    = datetime.utcnow().strftime("%d %b %Y")

    if len(source_files) == 1:
        guide = _format_single_source(results, original_query)
    else:
        guide = _format_multi_source(results, original_query)

    footer = (
        f"\n{'─' * 50}\n"
        f"This guide was automatically retrieved from the "
        f"IT Knowledge Base ({timestamp}).\n"
        f"If these steps do not resolve your issue, an engineer "
        f"will follow up with you shortly.\n"
        f"Please let us know if this guide was helpful."
    )

    return guide + footer


def _format_single_source(results: list, query: str) -> str:
    """
    Format results from a single source document.

    Args:
        results : List of result dicts from one source file
        query   : Original query for context

    Returns:
        Formatted guide string
    """
    file_name  = results[0]["file_name"]
    guide_name = _file_name_to_title(file_name)
    top_score  = results[0]["score"]

    header = (
        f"SELF-HELP GUIDE: {guide_name}\n"
        f"{'═' * 50}\n"
        f"Relevance: {_score_to_label(top_score)}\n\n"
    )

    body_parts = []
    for result in results:
        cleaned = _clean_chunk_text(result["text"])
        if cleaned:
            body_parts.append(cleaned)

    body = "\n\n".join(body_parts)

    return header + body


def _format_multi_source(results: list, query: str) -> str:
    """
    Format results from multiple source documents.
    Groups chunks by source file and adds section headers.

    Args:
        results : List of result dicts from multiple source files
        query   : Original query for context

    Returns:
        Formatted guide string with section headers
    """
    header = (
        f"SELF-HELP GUIDES\n"
        f"{'═' * 50}\n"
        f"We found relevant guides from multiple sources:\n\n"
    )

    grouped = {}
    for result in results:
        fname = result["file_name"]
        if fname not in grouped:
            grouped[fname] = []
        grouped[fname].append(result)

    sections = []
    for file_name, file_results in grouped.items():
        title     = _file_name_to_title(file_name)
        top_score = file_results[0]["score"]

        section_header = (
            f"{'─' * 50}\n"
            f"{title}\n"
            f"Relevance: {_score_to_label(top_score)}\n"
            f"{'─' * 50}\n"
        )

        body_parts = []
        for result in file_results:
            cleaned = _clean_chunk_text(result["text"])
            if cleaned:
                body_parts.append(cleaned)

        section_body = "\n\n".join(body_parts)
        sections.append(section_header + section_body)

    return header + "\n\n".join(sections)


def _clean_chunk_text(text: str) -> str:
    """
    Clean chunk text for display in the formatted guide.
    Normalizes whitespace and removes artifacts from chunking.

    Args:
        text : Raw chunk text from ChromaDB

    Returns:
        Cleaned display text
    """
    if not text:
        return ""

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' \n', '\n', text)
    text = text.strip()

    return text


def _file_name_to_title(file_name: str) -> str:
    """
    Convert a filename into a readable guide title.
    e.g. 'vpn_setup_guide.txt' → 'VPN Setup Guide'

    Args:
        file_name : Source document filename

    Returns:
        Human-readable title string
    """
    name = os.path.splitext(file_name)[0]
    name = name.replace("_", " ").replace("-", " ")
    name = " ".join(w.capitalize() for w in name.split())

    overrides = {
        "Vpn Setup Guide"            : "VPN Setup Guide",
        "Antivirus Guide"            : "Antivirus Troubleshooting Guide",
        "Password Reset Guide"       : "Password Reset Guide",
        "Printer Guide"              : "Printer Troubleshooting Guide",
        "Outlook Guide"              : "Microsoft Outlook Troubleshooting Guide",
        "Network Guide"              : "Network Troubleshooting Guide",
        "Os Issue Guide"             : "Windows OS Troubleshooting Guide",
        "App Install Guide"          : "Software Installation Guide",
        "Access Permission Guide"    : "Access and Permission Guide",
    }

    return overrides.get(name, name)


def _score_to_label(score: float) -> str:
    """
    Convert a numeric similarity score to a readable label.

    Args:
        score : Cosine similarity score between 0.0 and 1.0

    Returns:
        Label string with score
    """
    if score >= 0.75:
        label = "High"
    elif score >= 0.50:
        label = "Medium"
    elif score >= 0.30:
        label = "Low"
    else:
        label = "Very Low"

    return f"{label} ({score:.0%})"


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 65)
    print("KB SEARCH — TEST RUN")
    print("=" * 65 + "\n")

    print("Checking KB availability...")
    available = is_kb_available()

    if not available:
        print(
            "KB index not found or empty.\n"
            "Running kb_indexer.py to build index first...\n"
        )
        import sys
        sys.path.append(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        from knowledge_base.kb_indexer import (
            create_sample_docs,
            build_index,
        )
        create_sample_docs()
        build_index(force_rebuild=True)
        available = is_kb_available()

        if not available:
            print("Failed to build index. Check logs.")
            exit(1)

    stats = get_kb_stats()
    print(f"KB Status      : Available")
    print(f"Total Chunks   : {stats['total_chunks']}")
    print(f"Collection     : {stats['collection_name']}")
    print(f"Embed Model    : {stats['embed_model']}")

    print("\n" + "=" * 65)
    print("SEARCH TEST CASES")
    print("=" * 65)

    test_queries = [
        {
            "label"      : "VPN not connecting",
            "query"      : (
                "I cannot connect to VPN from home. "
                "Cisco AnyConnect shows connection timed out. "
                "I need to access company files urgently."
            ),
        },
        {
            "label"      : "Antivirus out of date",
            "query"      : (
                "My Symantec antivirus is showing a red warning. "
                "The virus definitions are out of date. "
                "LiveUpdate keeps failing."
            ),
        },
        {
            "label"      : "Password reset",
            "query"      : (
                "I forgot my Windows password and now my "
                "account is locked out. I cannot log in "
                "to my laptop."
            ),
        },
        {
            "label"      : "Outlook crashing",
            "query"      : (
                "Outlook is not opening this morning. "
                "It crashes immediately on startup. "
                "I cannot send or receive emails."
            ),
        },
        {
            "label"      : "Printer offline",
            "query"      : (
                "My printer is showing as offline. "
                "I cannot print any documents. "
                "The print queue is stuck."
            ),
        },
        {
            "label"      : "Category search — network",
            "query"      : None,
            "category"   : "network",
        },
        {
            "label"      : "Multi-query — VPN and Outlook",
            "queries"    : [
                "VPN not connecting from home",
                "Outlook not opening email not working",
            ],
        },
        {
            "label"      : "Short query — should still work",
            "query"      : "printer not printing",
        },
        {
            "label"      : "Unrelated query — should return None",
            "query"      : (
                "I want to order a new office chair and "
                "request more stationery supplies for my desk."
            ),
        },
    ]

    for i, tc in enumerate(test_queries, start=1):
        label = tc["label"]
        print(f"\n[Test {i}] {label}")
        print("-" * 55)

        if "category" in tc:
            result = search_by_category(tc["category"])

        elif "queries" in tc:
            result = search_multi_query(tc["queries"])

        else:
            result = search_knowledge_base(tc["query"])

        if result:
            preview = result[:300].replace("\n", " ")
            print(f"Result   : FOUND")
            print(f"Preview  : {preview}...")

            if "queries" not in tc and "category" not in tc:
                details = search_with_details(tc["query"])
                if details:
                    print(f"Sources  :", end="")
                    for d in details:
                        print(
                            f"\n  [{d['rank']}] "
                            f"{d['file_name']} "
                            f"| score: {d['score']:.3f} "
                            f"| chunk: {d['chunk_index']}"
                        )
        else:
            print("Result   : NOT FOUND (no relevant guide)")

    print("\n" + "=" * 65)
    print("All KB search tests complete.")
    print("=" * 65)