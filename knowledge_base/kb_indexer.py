import os
import logging
import hashlib
import json
from datetime   import datetime
from pathlib    import Path
from dotenv     import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

DOCS_DIR       = os.getenv("KB_DOCS_DIR",    "knowledge_base/docs")
CHROMA_DIR     = os.getenv("KB_CHROMA_DIR",  "knowledge_base/chroma_db")
METADATA_FILE  = os.getenv("KB_METADATA",    "knowledge_base/index_metadata.json")
COLLECTION_NAME = "it_support_kb"
CHUNK_SIZE      = int(os.getenv("KB_CHUNK_SIZE",  500))
CHUNK_OVERLAP   = int(os.getenv("KB_CHUNK_OVERLAP", 50))

SUPPORTED_EXTENSIONS = [".txt", ".md", ".rst"]


def build_index(force_rebuild: bool = False) -> bool:
    """
    Main entry point — scans docs/ folder, processes all
    documents into chunks, and stores them in ChromaDB.

    Flow:
        1. Scan docs/ folder for supported files
        2. Check which files are new or changed since last index
        3. Load and chunk changed documents
        4. Generate embeddings and store in ChromaDB
        5. Save metadata so next run skips unchanged files

    Args:
        force_rebuild : If True, re-indexes everything even
                        if files have not changed

    Returns:
        True if indexing completed successfully, False otherwise
    """
    log.info("=" * 55)
    log.info("KB INDEXER — Starting build")
    log.info("=" * 55)

    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError:
        log.error(
            "chromadb not installed. Run:\n"
            "  pip install chromadb sentence-transformers"
        )
        return False

    os.makedirs(DOCS_DIR,   exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)

    doc_files = _scan_docs_folder()

    if not doc_files:
        log.warning(
            f"No documents found in '{DOCS_DIR}'. "
            "Add .txt or .md files to knowledge_base/docs/ and re-run."
        )
        return False

    log.info(f"Found {len(doc_files)} document(s) in docs folder.")

    metadata      = _load_metadata()
    files_to_index = (
        doc_files if force_rebuild
        else _get_changed_files(doc_files, metadata)
    )

    if not files_to_index:
        log.info("All documents are up to date. Nothing to re-index.")
        return True

    log.info(
        f"{len(files_to_index)} file(s) to index "
        f"({'force rebuild' if force_rebuild else 'new or changed'})."
    )

    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        embed_fn      = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        try:
            collection = chroma_client.get_collection(
                name              = COLLECTION_NAME,
                embedding_function = embed_fn,
            )
            log.info(
                f"Loaded existing ChromaDB collection "
                f"'{COLLECTION_NAME}' with "
                f"{collection.count()} existing chunks."
            )
        except Exception:
            collection = chroma_client.create_collection(
                name              = COLLECTION_NAME,
                embedding_function = embed_fn,
                metadata          = {"hnsw:space": "cosine"},
            )
            log.info(f"Created new ChromaDB collection '{COLLECTION_NAME}'.")

    except Exception as e:
        log.error(f"Failed to initialize ChromaDB: {e}")
        return False

    total_chunks  = 0
    indexed_files = 0

    for file_path in files_to_index:
        log.info(f"Indexing: {file_path.name}")

        raw_text = _load_document(file_path)
        if not raw_text:
            log.warning(f"Skipping empty file: {file_path.name}")
            continue

        chunks = _chunk_text(
            text      = raw_text,
            file_name = file_path.name,
        )

        if not chunks:
            log.warning(f"No chunks generated for: {file_path.name}")
            continue

        _remove_existing_chunks(collection, file_path.name)

        success = _add_chunks_to_collection(
            collection = collection,
            chunks     = chunks,
            file_name  = file_path.name,
        )

        if success:
            metadata[file_path.name] = {
                "hash"        : _hash_file(file_path),
                "indexed_at"  : datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "chunk_count" : len(chunks),
                "file_size"   : file_path.stat().st_size,
            }
            total_chunks  += len(chunks)
            indexed_files += 1
            log.info(
                f"  Indexed {len(chunks)} chunk(s) "
                f"from '{file_path.name}'."
            )
        else:
            log.error(f"Failed to index: {file_path.name}")

    _save_metadata(metadata)

    log.info("=" * 55)
    log.info(
        f"KB INDEX COMPLETE — "
        f"{indexed_files} file(s), "
        f"{total_chunks} total chunk(s)."
    )
    log.info(f"Total documents in collection: {collection.count()}")
    log.info("=" * 55)

    return True


def _scan_docs_folder() -> list:
    """
    Scan the docs/ directory and return all supported document files.

    Returns:
        List of Path objects for each supported document file
    """
    docs_path = Path(DOCS_DIR)

    if not docs_path.exists():
        log.error(f"Docs folder does not exist: {DOCS_DIR}")
        return []

    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(docs_path.rglob(f"*{ext}"))

    files = sorted(files)

    log.info(f"Scanned docs folder — found {len(files)} file(s):")
    for f in files:
        size_kb = f.stat().st_size / 1024
        log.info(f"  {f.name:<40} ({size_kb:.1f} KB)")

    return files


def _load_document(file_path: Path) -> str:
    """
    Read a document file and return its text content.
    Handles encoding issues gracefully.

    Args:
        file_path : Path object pointing to the document file

    Returns:
        Document text string or empty string on failure
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()
        log.debug(
            f"Loaded '{file_path.name}' "
            f"({len(text)} characters)"
        )
        return text

    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read().strip()
            log.warning(
                f"File '{file_path.name}' read with latin-1 encoding "
                "(consider saving as UTF-8)."
            )
            return text
        except Exception as e:
            log.error(
                f"Cannot read file '{file_path.name}': {e}"
            )
            return ""

    except Exception as e:
        log.error(f"Error loading document '{file_path.name}': {e}")
        return ""


def _chunk_text(text: str, file_name: str) -> list:
    """
    Split a document into overlapping chunks for indexing.

    Chunking strategy:
        1. Split by paragraphs first (double newlines)
        2. If a paragraph is longer than CHUNK_SIZE words,
           split it further by sentences
        3. Merge small adjacent chunks so no chunk is
           too small to be useful
        4. Add CHUNK_OVERLAP words of context from the
           previous chunk to the start of each new chunk

    Args:
        text      : Full document text to split
        file_name : Document filename (used in chunk metadata)

    Returns:
        List of chunk dicts with keys:
            text, chunk_id, file_name, chunk_index, word_count
    """
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    raw_chunks = []
    for para in paragraphs:
        words = para.split()

        if len(words) <= CHUNK_SIZE:
            raw_chunks.append(para)
        else:
            sentences  = _split_into_sentences(para)
            current    = []
            word_count = 0

            for sentence in sentences:
                sentence_words = sentence.split()

                if word_count + len(sentence_words) > CHUNK_SIZE and current:
                    raw_chunks.append(" ".join(current))
                    overlap_words = current[-CHUNK_OVERLAP:] if CHUNK_OVERLAP > 0 else []
                    current       = overlap_words + sentence_words
                    word_count    = len(current)
                else:
                    current.extend(sentence_words)
                    word_count += len(sentence_words)

            if current:
                raw_chunks.append(" ".join(current))

    merged_chunks = _merge_small_chunks(raw_chunks, min_words=30)

    chunks = []
    prev_words = []

    for idx, chunk_text in enumerate(merged_chunks):
        if prev_words and CHUNK_OVERLAP > 0:
            overlap    = " ".join(prev_words[-CHUNK_OVERLAP:])
            chunk_text = f"{overlap} {chunk_text}"

        chunk_id = _generate_chunk_id(file_name, idx, chunk_text)

        chunks.append({
            "text"        : chunk_text.strip(),
            "chunk_id"    : chunk_id,
            "file_name"   : file_name,
            "chunk_index" : idx,
            "word_count"  : len(chunk_text.split()),
        })

        prev_words = chunk_text.split()

    log.debug(
        f"Chunked '{file_name}' into "
        f"{len(chunks)} chunk(s)."
    )

    return chunks


def _split_into_sentences(text: str) -> list:
    """
    Split a paragraph into individual sentences.
    Uses punctuation-based splitting with common abbreviation
    handling so "Dr." and "e.g." do not cause false splits.

    Args:
        text : Paragraph text to split

    Returns:
        List of sentence strings
    """
    import re

    abbreviations = [
        "dr", "mr", "mrs", "ms", "prof", "sr", "jr",
        "vs", "etc", "e.g", "i.e", "fig", "no",
        "jan", "feb", "mar", "apr", "jun", "jul",
        "aug", "sep", "oct", "nov", "dec",
    ]

    protected = text
    for abbr in abbreviations:
        protected = protected.replace(
            f"{abbr}.",
            f"{abbr}<DOT>"
        )
        protected = protected.replace(
            f"{abbr.title()}.",
            f"{abbr.title()}<DOT>"
        )

    sentences = re.split(r'(?<=[.!?])\s+', protected)

    sentences = [
        s.replace("<DOT>", ".").strip()
        for s in sentences if s.strip()
    ]

    return sentences


def _merge_small_chunks(chunks: list, min_words: int = 30) -> list:
    """
    Merge chunks that are too small (under min_words) with
    the next chunk so every chunk has enough context to be useful.

    Args:
        chunks    : List of raw chunk text strings
        min_words : Minimum word count — chunks below this are merged

    Returns:
        List of merged chunk text strings
    """
    if not chunks:
        return []

    merged = []
    buffer = ""

    for chunk in chunks:
        if buffer:
            combined = f"{buffer} {chunk}"
        else:
            combined = chunk

        if len(combined.split()) >= min_words:
            merged.append(combined.strip())
            buffer = ""
        else:
            buffer = combined

    if buffer:
        if merged:
            merged[-1] = f"{merged[-1]} {buffer}".strip()
        else:
            merged.append(buffer.strip())

    return merged


def _add_chunks_to_collection(
    collection,
    chunks    : list,
    file_name : str,
) -> bool:
    """
    Add a list of text chunks to the ChromaDB collection.
    Batches inserts in groups of 50 to avoid memory issues
    with large documents.

    Args:
        collection : ChromaDB collection object
        chunks     : List of chunk dicts from _chunk_text()
        file_name  : Source document filename

    Returns:
        True if all chunks were added successfully
    """
    if not chunks:
        return False

    BATCH_SIZE = 50

    try:
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]

            ids        = [c["chunk_id"]    for c in batch]
            documents  = [c["text"]        for c in batch]
            metadatas  = [
                {
                    "file_name"   : c["file_name"],
                    "chunk_index" : c["chunk_index"],
                    "word_count"  : c["word_count"],
                    "indexed_at"  : datetime.utcnow().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
                for c in batch
            ]

            collection.add(
                ids       = ids,
                documents = documents,
                metadatas = metadatas,
            )

            log.debug(
                f"  Batch {i // BATCH_SIZE + 1}: "
                f"Added {len(batch)} chunk(s) from '{file_name}'."
            )

        return True

    except Exception as e:
        log.error(
            f"Failed to add chunks from '{file_name}' "
            f"to ChromaDB: {e}"
        )
        return False


def _remove_existing_chunks(collection, file_name: str) -> None:
    """
    Delete all existing chunks from a specific file before
    re-indexing it. Prevents duplicate entries when a file
    is updated and re-indexed.

    Args:
        collection : ChromaDB collection object
        file_name  : Source document filename to remove chunks for
    """
    try:
        existing = collection.get(
            where={"file_name": file_name}
        )

        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
            log.info(
                f"Removed {len(existing['ids'])} existing "
                f"chunk(s) for '{file_name}' before re-indexing."
            )

    except Exception as e:
        log.warning(
            f"Could not remove existing chunks "
            f"for '{file_name}': {e}"
        )


def _get_changed_files(
    doc_files : list,
    metadata  : dict,
) -> list:
    """
    Compare current file hashes against stored metadata to
    find only files that are new or have been modified since
    the last index run.

    Args:
        doc_files : List of Path objects from _scan_docs_folder()
        metadata  : Dict loaded from index_metadata.json

    Returns:
        List of Path objects for files that need re-indexing
    """
    changed = []

    for file_path in doc_files:
        file_name     = file_path.name
        current_hash  = _hash_file(file_path)
        stored_meta   = metadata.get(file_name, {})
        stored_hash   = stored_meta.get("hash", "")

        if current_hash != stored_hash:
            reason = (
                "new file" if not stored_hash
                else "file changed"
            )
            log.info(
                f"  {file_name} — {reason} "
                f"(will re-index)"
            )
            changed.append(file_path)
        else:
            log.debug(f"  {file_name} — unchanged (skipping)")

    return changed


def _hash_file(file_path: Path) -> str:
    """
    Calculate MD5 hash of a file for change detection.
    Fast and sufficient for detecting file modifications.

    Args:
        file_path : Path object pointing to the file

    Returns:
        MD5 hex digest string
    """
    try:
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        log.error(f"Cannot hash file '{file_path.name}': {e}")
        return ""


def _generate_chunk_id(
    file_name   : str,
    chunk_index : int,
    chunk_text  : str,
) -> str:
    """
    Generate a stable unique ID for a chunk.
    ID is based on file name + chunk index + content hash
    so the same chunk always gets the same ID even across
    multiple index runs.

    Args:
        file_name   : Source document filename
        chunk_index : Position of this chunk in the document
        chunk_text  : The chunk text content

    Returns:
        Unique chunk ID string
    """
    content    = f"{file_name}:{chunk_index}:{chunk_text[:100]}"
    short_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    safe_name  = file_name.replace(".", "_").replace(" ", "_")
    return f"{safe_name}_chunk_{chunk_index:04d}_{short_hash}"


def _load_metadata() -> dict:
    """
    Load the index metadata JSON file that tracks which
    files have been indexed and their content hashes.

    Returns:
        Dict of filename -> metadata dict
        Empty dict if file does not exist yet
    """
    if not os.path.exists(METADATA_FILE):
        log.info("No existing metadata file — fresh index.")
        return {}

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        log.info(
            f"Loaded metadata for "
            f"{len(metadata)} previously indexed file(s)."
        )
        return metadata

    except json.JSONDecodeError as e:
        log.warning(f"Metadata file is corrupt: {e}. Starting fresh.")
        return {}

    except Exception as e:
        log.error(f"Cannot load metadata: {e}")
        return {}


def _save_metadata(metadata: dict) -> None:
    """
    Save the updated index metadata to JSON file.
    Called after every successful index run.

    Args:
        metadata : Dict of filename -> metadata dict to save
    """
    try:
        os.makedirs(
            os.path.dirname(METADATA_FILE),
            exist_ok=True
        )
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        log.info(
            f"Metadata saved for "
            f"{len(metadata)} indexed file(s)."
        )

    except Exception as e:
        log.error(f"Cannot save metadata: {e}")


def get_index_stats() -> dict:
    """
    Return statistics about the current ChromaDB index.
    Useful for verifying the index is built correctly.

    Returns:
        Dict with total_chunks, collection_name,
        indexed_files, chroma_dir
    """
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        client = chromadb.PersistentClient(path=CHROMA_DIR)
        embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        try:
            collection = client.get_collection(
                name               = COLLECTION_NAME,
                embedding_function = embed_fn,
            )
            total_chunks = collection.count()
        except Exception:
            total_chunks = 0

        metadata      = _load_metadata()
        indexed_files = len(metadata)

        return {
            "collection_name" : COLLECTION_NAME,
            "total_chunks"    : total_chunks,
            "indexed_files"   : indexed_files,
            "chroma_dir"      : CHROMA_DIR,
            "docs_dir"        : DOCS_DIR,
            "metadata"        : metadata,
        }

    except ImportError:
        return {
            "collection_name" : COLLECTION_NAME,
            "total_chunks"    : 0,
            "indexed_files"   : 0,
            "chroma_dir"      : CHROMA_DIR,
            "docs_dir"        : DOCS_DIR,
            "error"           : "chromadb not installed",
        }

    except Exception as e:
        log.error(f"Cannot get index stats: {e}")
        return {"error": str(e)}


def delete_index() -> bool:
    """
    Completely delete the ChromaDB index and metadata.
    Use this to do a clean rebuild from scratch.
    WARNING — all indexed data will be lost.

    Returns:
        True if deleted successfully
    """
    import shutil

    log.warning("Deleting ChromaDB index and metadata...")

    try:
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
            log.info(f"Deleted ChromaDB directory: {CHROMA_DIR}")

        if os.path.exists(METADATA_FILE):
            os.remove(METADATA_FILE)
            log.info(f"Deleted metadata file: {METADATA_FILE}")

        log.info("Index deleted. Run build_index() to rebuild.")
        return True

    except Exception as e:
        log.error(f"Failed to delete index: {e}")
        return False


def create_sample_docs() -> None:
    """
    Create sample IT support guide documents in the docs/ folder.
    Run this once to populate the knowledge base with starter
    content so you can test the indexer immediately.
    """
    os.makedirs(DOCS_DIR, exist_ok=True)

    docs = {
        "vpn_setup_guide.txt": """
VPN Connection Guide — Cisco AnyConnect

This guide explains how to connect to the company VPN using
Cisco AnyConnect on Windows 10 and Windows 11.

Step 1 — Open Cisco AnyConnect
Open the Start menu and search for Cisco AnyConnect.
Click on the Cisco AnyConnect Secure Mobility Client icon.
If AnyConnect is not installed, contact IT support to install it.

Step 2 — Enter VPN Server Address
In the connection box enter: vpn.icici.com
Click the Connect button.

Step 3 — Enter Your Credentials
Username: Enter your Windows domain username (same as your laptop login).
Password: Enter your current Windows password.
Click OK to connect.

Step 4 — Verify Connection
A green lock icon will appear in the taskbar when connected.
You can now access all company network resources and shared drives.

Troubleshooting VPN Issues

Issue: Connection timed out
Solution: Check your internet connection first. Try disconnecting and reconnecting.
If the issue persists, restart the Cisco AnyConnect service:
Open Task Manager, go to Services tab, find vpnagent, right click and restart.

Issue: Invalid credentials error
Solution: Make sure your Windows password has not expired.
Try logging into your laptop first to confirm your password is correct.
If your password has expired, contact IT support for a reset.

Issue: VPN connects but cannot access network drives
Solution: After connecting to VPN, open File Explorer and type
\\fileserver01 in the address bar to access shared drives.
If this fails, disconnect and reconnect to VPN and try again.

Issue: AnyConnect not installed
Solution: Raise a ticket with IT support requesting Cisco AnyConnect installation.
Our team will push it to your machine remotely within 2 hours.
""",

        "antivirus_guide.txt": """
Antivirus Troubleshooting Guide — Windows Defender and Symantec

This guide covers common antivirus issues and how to resolve them
on ICICI Bank corporate laptops and desktops.

Windows Defender Issues

Issue: Real-time protection is turned off
Solution: Open Windows Security from the Start menu.
Click Virus and threat protection.
Under Virus and threat protection settings click Manage settings.
Toggle Real-time protection to On.
If it keeps turning off automatically, your machine may have a conflicting
antivirus program. Contact IT support.

Issue: Windows Defender definitions are out of date
Solution: Open Windows Security and click Virus and threat protection.
Click Check for updates under Virus and threat protection updates.
Click Check for updates button.
Allow the update to complete. This may take 5 to 10 minutes.
If updates fail, restart your computer and try again.

Issue: Windows Defender scan failed or stuck
Solution: Open Task Manager and end the MsMpEng process.
Wait 30 seconds then open Windows Security and start a new quick scan.
If scans continue to fail, contact IT support to run a remote repair.

Symantec Endpoint Protection Issues

Issue: Symantec showing red warning icon
Solution: Right click the Symantec icon in the taskbar.
Select Open Symantec Endpoint Protection.
Click LiveUpdate to download the latest definitions.
Wait for the update to complete then verify the icon turns green.

Issue: Symantec LiveUpdate fails repeatedly
Solution: This is often caused by proxy or network issues.
Contact IT support who will push a manual definition update
remotely to your machine.

Issue: Symantec scan detected a threat
Solution: Do not open or delete the file manually.
Let Symantec quarantine it automatically.
Contact IT support immediately with the threat name shown.
Do not connect USB drives or external devices to your machine.

General Antivirus Best Practices
Never disable antivirus protection even temporarily.
Do not click on email attachments from unknown senders.
Report suspicious files or popups to IT support immediately.
Keep your operating system and antivirus up to date at all times.
""",

        "password_reset_guide.txt": """
Password Reset Guide — Windows and Corporate Accounts

This guide explains how to reset your Windows domain password,
unlock your account, and resolve MFA issues at ICICI Bank.

How to Change Your Password Before It Expires

Press Ctrl plus Alt plus Delete on your keyboard.
Click Change a password.
Enter your current password in the Old password field.
Enter your new password twice in the New password fields.
Click the arrow button to confirm.
Password requirements: Minimum 8 characters, at least one uppercase letter,
one lowercase letter, one number, and one special character.
Password cannot be the same as your last 10 passwords.

How to Reset a Forgotten Password

If you have forgotten your password and are locked out:
Option 1 — Self service portal: Go to password.icici.com
Click Forgot Password and follow the steps using your registered mobile number.
Option 2 — Contact IT support: Raise a ticket or call the helpdesk.
IT support will reset your password and send you a temporary password via SMS.
You will be required to change it on first login.

Account Locked Out

Your account locks after 5 incorrect password attempts.
Wait 15 minutes for the automatic unlock.
Or contact IT support for an immediate unlock.
IT will verify your identity before unlocking.

MFA and Authenticator Issues

Issue: Microsoft Authenticator not generating codes
Solution: Check the time on your phone is correct and set to automatic.
Open Authenticator app, tap the three dots menu, tap Refresh accounts.
If codes still fail, contact IT support to re-register your device.

Issue: OTP SMS not received
Solution: Check your registered mobile number with IT support.
Try requesting OTP again after 60 seconds.
Check if your phone has signal or is on Do Not Disturb.
Contact IT support if OTP consistently fails to arrive.

Issue: MFA prompt not appearing
Solution: Clear your browser cache and cookies.
Try a different browser such as Chrome or Edge.
Contact IT support if the issue persists.
""",

        "printer_guide.txt": """
Printer Troubleshooting Guide — Corporate Printers

This guide covers common printer issues on ICICI Bank
corporate network printers.

Issue: Printer showing as Offline

Step 1: Check the printer is powered on and has paper loaded.
Step 2: Open Control Panel, go to Devices and Printers.
Step 3: Right click your printer and click See what is printing.
Step 4: In the print queue window click Printer menu at the top.
Step 5: Uncheck Use Printer Offline if it is checked.
Step 6: If still offline, right click the printer and Set as default printer.
Step 7: Restart the Print Spooler service:
  Open Run dialog with Windows plus R.
  Type services.msc and press Enter.
  Find Print Spooler in the list.
  Right click and select Restart.
Try printing a test page after the spooler restarts.

Issue: Print Queue Stuck or Documents Not Printing

Step 1: Open Devices and Printers from Control Panel.
Step 2: Double click the printer to open the print queue.
Step 3: Select all jobs with Ctrl plus A.
Step 4: Click Document menu and select Cancel.
Step 5: If jobs cannot be cancelled, clear the queue manually:
  Stop the Print Spooler service in services.msc.
  Open File Explorer and go to C:\\Windows\\System32\\spool\\PRINTERS
  Delete all files in this folder (do not delete the folder itself).
  Start the Print Spooler service again.
Try printing again after clearing the queue.

Issue: Printer Driver Missing or Outdated

Raise an IT support ticket requesting a printer driver update.
Our team will push the latest driver to your machine remotely.
Specify the printer model name in your ticket for faster resolution.

Issue: Cannot Find Network Printer

Step 1: Make sure you are connected to the office network or VPN.
Step 2: Open Run dialog and type \\\\printserver01 and press Enter.
Step 3: You will see all available network printers.
Step 4: Right click the printer you need and select Connect.
Step 5: The printer will install automatically.

Issue: Paper Jam

Step 1: Turn off the printer completely.
Step 2: Open all paper trays and doors to locate jammed paper.
Step 3: Gently pull the jammed paper out in the direction it travels.
Never pull paper backwards as this damages the rollers.
Step 4: Remove any torn paper pieces completely.
Step 5: Close all doors and turn the printer back on.
If the jam error persists after clearing, contact IT support.
""",

        "outlook_guide.txt": """
Microsoft Outlook Troubleshooting Guide

This guide covers common Outlook and email issues on ICICI Bank
corporate laptops.

Issue: Outlook Not Opening or Crashing on Startup

Step 1: Close Outlook completely including from the system tray.
Step 2: Open Run dialog with Windows plus R.
Step 3: Type outlook.exe /safe and press Enter.
This opens Outlook in Safe Mode without add-ins.
If Outlook opens in Safe Mode, an add-in is causing the crash.
Go to File, Options, Add-ins and disable all add-ins.
Restart Outlook normally and re-enable add-ins one by one to identify the problem.

Step 4: If Outlook does not open even in Safe Mode, repair Office:
Go to Control Panel, Programs, Programs and Features.
Right click Microsoft Office and select Change.
Select Quick Repair and click Repair.

Issue: Emails Not Sending or Receiving

Step 1: Check your internet connection is working.
Step 2: Look at the status bar at the bottom of Outlook.
It should say Connected to Microsoft Exchange.
If it says Disconnected or Working Offline:
Click Send/Receive tab and uncheck Work Offline.

Step 3: Check your Outbox folder for stuck emails.
If emails are stuck in Outbox, delete the stuck email and try sending again.

Step 4: If emails are not arriving, check your Junk Email folder.
Check with the sender if they received any bounce-back error messages.

Issue: Outlook Very Slow or Freezing

Step 1: Your PST or OST data file may be too large.
Go to File, Account Settings, Data Files to check the file size.
If the file is over 10 GB contact IT support to archive old emails.

Step 2: Disable unnecessary add-ins in File, Options, Add-ins.

Step 3: Compact the data file:
Go to File, Account Settings, Data Files.
Select your data file and click Settings.
Click Compact Now and wait for it to finish.

Issue: PST File Corrupt

If Outlook shows an error about a corrupt PST file:
Do not delete the PST file manually.
Raise an IT support ticket immediately.
Our team will run scanpst.exe remotely to repair the file.
Regular backups of PST files are performed automatically by IT.

Issue: Cannot Connect to Exchange Server

Check you are connected to the office network or VPN.
If working from home, ensure VPN is connected before opening Outlook.
Restart Outlook after connecting to VPN.
If the issue persists after connecting to VPN, contact IT support.

Outlook Best Practices
Keep your Inbox organized by creating folders for different projects.
Empty your Deleted Items and Junk Email folders regularly.
Archive emails older than 6 months to keep mailbox size manageable.
Never store sensitive passwords or confidential data in email.
""",
    }

    for filename, content in docs.items():
        file_path = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip())
            log.info(f"Created sample doc: {filename}")
        else:
            log.info(f"Sample doc already exists: {filename}")

    log.info(
        f"Sample documents ready in '{DOCS_DIR}'. "
        "Run build_index() to index them."
    )


if __name__ == "__main__":
    logging.basicConfig(
        level  = logging.INFO,
        format = "%(asctime)s [%(levelname)s] %(message)s"
    )

    print("\n" + "=" * 60)
    print("KB INDEXER — TEST RUN")
    print("=" * 60 + "\n")

    print("Step 1: Creating sample documents...")
    create_sample_docs()

    print("\nStep 2: Building index...")
    success = build_index(force_rebuild=False)

    if success:
        print("\nStep 3: Index statistics:")
        stats = get_index_stats()
        print(f"  Collection   : {stats['collection_name']}")
        print(f"  Total chunks : {stats['total_chunks']}")
        print(f"  Indexed files: {stats['indexed_files']}")
        print(f"  Chroma dir   : {stats['chroma_dir']}")

        print("\nIndexed files:")
        for fname, meta in stats.get("metadata", {}).items():
            print(
                f"  {fname:<40} "
                f"| {meta['chunk_count']} chunks "
                f"| {meta['indexed_at']}"
            )

        print("\nStep 4: Testing incremental update (no changes)...")
        success2 = build_index(force_rebuild=False)
        print(
            f"Second run result: "
            f"{'No re-index needed' if success2 else 'Failed'}"
        )

        print("\nStep 5: Force rebuild test...")
        success3 = build_index(force_rebuild=True)
        print(f"Force rebuild result: {'SUCCESS' if success3 else 'FAILED'}")

    else:
        print("Indexing failed — check logs above for errors.")

    print("\nKB Indexer test complete.")
    print("Next step: Run knowledge_base/kb_search.py to test searching.")