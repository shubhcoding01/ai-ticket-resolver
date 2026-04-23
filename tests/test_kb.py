import os
import sys
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib       import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


TEMP_DIR      = tempfile.mkdtemp(prefix="kb_test_")
TEST_DOCS_DIR = os.path.join(TEMP_DIR, "docs")
TEST_CHROMA   = os.path.join(TEMP_DIR, "chroma_db")
TEST_METADATA = os.path.join(TEMP_DIR, "index_metadata.json")

os.makedirs(TEST_DOCS_DIR, exist_ok=True)

os.environ["KB_DOCS_DIR"]    = TEST_DOCS_DIR
os.environ["KB_CHROMA_DIR"]  = TEST_CHROMA
os.environ["KB_METADATA"]    = TEST_METADATA

from knowledge_base.kb_indexer import (
    build_index,
    _scan_docs_folder,
    _load_document,
    _chunk_text,
    _split_into_sentences,
    _merge_small_chunks,
    _hash_file,
    _generate_chunk_id,
    _load_metadata,
    _save_metadata,
    _get_changed_files,
    get_index_stats,
    create_sample_docs,
    DOCS_DIR,
    CHROMA_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from knowledge_base.kb_search import (
    search_knowledge_base,
    search_with_details,
    search_by_category,
    search_multi_query,
    is_kb_available,
    get_kb_stats,
    _clean_query,
    _filter_by_score,
    _deduplicate_results,
    _text_overlap_ratio,
    _format_guide,
    _file_name_to_title,
    _score_to_label,
    _clean_chunk_text,
)


SAMPLE_DOC_CONTENT = """
VPN Connection Guide

This guide explains how to connect to the company VPN.

Step 1 — Open Cisco AnyConnect
Open the Start menu and search for Cisco AnyConnect.
Click on the application icon to open it.

Step 2 — Enter Server Address
Type vpn.company.com in the connection box.
Click Connect to proceed.

Step 3 — Enter Credentials
Enter your domain username and password.
Click OK to complete the connection.

Troubleshooting VPN Issues

Issue: Connection timed out
Solution: Check your internet connection first.
Restart the AnyConnect service and try again.

Issue: Invalid credentials
Solution: Verify your password has not expired.
Contact IT support if the issue persists.
"""

ANTIVIRUS_DOC_CONTENT = """
Antivirus Troubleshooting Guide

This guide covers common antivirus issues on corporate laptops.

Windows Defender Issues

Issue: Real-time protection is turned off
Solution: Open Windows Security from the Start menu.
Toggle Real-time protection to On.

Issue: Definitions out of date
Solution: Open Windows Security and click Virus protection.
Click Check for updates to download latest definitions.

Symantec Endpoint Protection

Issue: Symantec showing red warning
Solution: Right click Symantec icon in taskbar.
Select Open and click LiveUpdate to update definitions.
"""


def _write_test_doc(filename: str, content: str) -> Path:
    """Write a test document to the test docs directory."""
    file_path = Path(TEST_DOCS_DIR) / filename
    file_path.write_text(content.strip(), encoding="utf-8")
    return file_path


def _cleanup_test_dir():
    """Remove the temp test directory after tests complete."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


class TestScanDocsFolder(unittest.TestCase):
    """Tests for _scan_docs_folder()."""

    def setUp(self):
        for f in Path(TEST_DOCS_DIR).glob("*"):
            f.unlink()

    def test_finds_txt_files(self):
        """Should find .txt files in docs folder."""
        _write_test_doc("test_guide.txt", "Some content here.")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertIn("test_guide.txt", names)

    def test_finds_md_files(self):
        """Should find .md files in docs folder."""
        _write_test_doc("test_guide.md", "# Some markdown here.")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertIn("test_guide.md", names)

    def test_ignores_unsupported_extensions(self):
        """Should not return .pdf or .docx files."""
        _write_test_doc("document.pdf",  "PDF content")
        _write_test_doc("document.docx", "DOCX content")
        files = _scan_docs_folder()
        names = [f.name for f in files]
        self.assertNotIn("document.pdf",  names)
        self.assertNotIn("document.docx", names)

    def test_empty_folder_returns_empty_list(self):
        """Empty docs folder returns empty list."""
        files = _scan_docs_folder()
        self.assertEqual(files, [])

    def test_returns_list_of_path_objects(self):
        """Should return list of Path objects."""
        _write_test_doc("guide.txt", "Content here.")
        files = _scan_docs_folder()
        for f in files:
            self.assertIsInstance(f, Path)

    def test_multiple_files_all_returned(self):
        """Multiple files should all be returned."""
        _write_test_doc("guide_a.txt", "Content A.")
        _write_test_doc("guide_b.txt", "Content B.")
        _write_test_doc("guide_c.md",  "Content C.")
        files = _scan_docs_folder()
        self.assertGreaterEqual(len(files), 3)


class TestLoadDocument(unittest.TestCase):
    """Tests for _load_document()."""

    def test_loads_text_content(self):
        """Should return file content as string."""
        fp   = _write_test_doc("load_test.txt", "Hello world content.")
        text = _load_document(fp)
        self.assertEqual(text, "Hello world content.")

    def test_returns_empty_for_missing_file(self):
        """Missing file should return empty string."""
        fp   = Path(TEST_DOCS_DIR) / "nonexistent_file.txt"
        text = _load_document(fp)
        self.assertEqual(text, "")

    def test_strips_leading_trailing_whitespace(self):
        """Content should be stripped of leading/trailing whitespace."""
        fp   = _write_test_doc("whitespace_test.txt", "  Content here.  ")
        text = _load_document(fp)
        self.assertEqual(text, "Content here.")

    def test_multiline_content_preserved(self):
        """Multi-line content should be preserved."""
        content = "Line one.\nLine two.\nLine three."
        fp      = _write_test_doc("multiline.txt", content)
        text    = _load_document(fp)
        self.assertIn("Line one.",   text)
        self.assertIn("Line two.",   text)
        self.assertIn("Line three.", text)

    def test_empty_file_returns_empty(self):
        """Empty file should return empty string."""
        fp = Path(TEST_DOCS_DIR) / "empty.txt"
        fp.write_text("", encoding="utf-8")
        text = _load_document(fp)
        self.assertEqual(text, "")


class TestChunkText(unittest.TestCase):
    """Tests for _chunk_text()."""

    def test_short_text_returns_one_chunk(self):
        """Short text under CHUNK_SIZE should produce one chunk."""
        text   = "This is a short document with a few words."
        chunks = _chunk_text(text, "test.txt")
        self.assertGreaterEqual(len(chunks), 1)

    def test_long_text_returns_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        text   = ("This is a sentence with content. " * 100)
        chunks = _chunk_text(text, "long_doc.txt")
        self.assertGreater(len(chunks), 1)

    def test_each_chunk_has_required_keys(self):
        """Each chunk must have text, chunk_id, file_name, etc."""
        text   = "Some content to chunk. " * 30
        chunks = _chunk_text(text, "test.txt")
        for chunk in chunks:
            self.assertIn("text",        chunk)
            self.assertIn("chunk_id",    chunk)
            self.assertIn("file_name",   chunk)
            self.assertIn("chunk_index", chunk)
            self.assertIn("word_count",  chunk)

    def test_chunk_ids_are_unique(self):
        """All chunk IDs should be unique."""
        text   = ("Content sentence here. " * 100)
        chunks = _chunk_text(text, "test.txt")
        ids    = [c["chunk_id"] for c in chunks]
        self.assertEqual(len(ids), len(set(ids)))

    def test_file_name_preserved_in_chunks(self):
        """file_name field must match the input filename."""
        text   = "Some content here. " * 20
        chunks = _chunk_text(text, "my_guide.txt")
        for chunk in chunks:
            self.assertEqual(chunk["file_name"], "my_guide.txt")

    def test_empty_text_returns_empty_list(self):
        """Empty text should return empty list."""
        chunks = _chunk_text("", "empty.txt")
        self.assertEqual(chunks, [])

    def test_chunk_word_count_matches_text(self):
        """word_count in chunk should match actual word count."""
        text   = "One two three four five six seven eight nine ten. " * 10
        chunks = _chunk_text(text, "count_test.txt")
        for chunk in chunks:
            actual_words = len(chunk["text"].split())
            self.assertAlmostEqual(
                chunk["word_count"],
                actual_words,
                delta=CHUNK_OVERLAP + 5,
            )

    def test_chunk_index_sequential(self):
        """Chunk indices should start at 0 and be sequential."""
        text   = "Lots of content here. " * 100
        chunks = _chunk_text(text, "test.txt")
        indices = [c["chunk_index"] for c in chunks]
        self.assertEqual(indices[0], 0)
        self.assertEqual(indices, list(range(len(chunks))))


class TestSplitIntoSentences(unittest.TestCase):
    """Tests for _split_into_sentences()."""

    def test_simple_sentences_split(self):
        """Three sentences should produce three results."""
        text   = "First sentence. Second sentence. Third sentence."
        result = _split_into_sentences(text)
        self.assertEqual(len(result), 3)

    def test_exclamation_splits_sentences(self):
        """Exclamation mark should also split sentences."""
        text   = "Urgent issue! Please fix it. Thank you."
        result = _split_into_sentences(text)
        self.assertGreaterEqual(len(result), 2)

    def test_abbreviations_not_split(self):
        """Dr. and Mr. should not cause false sentence splits."""
        text   = "Contact Dr. Smith about this. He works in IT."
        result = _split_into_sentences(text)
        self.assertGreaterEqual(len(result), 1)

    def test_empty_text_returns_empty_list(self):
        """Empty text returns empty list."""
        result = _split_into_sentences("")
        self.assertEqual(result, [])

    def test_single_sentence_returns_one_item(self):
        """Single sentence returns list with one item."""
        text   = "This is the only sentence here"
        result = _split_into_sentences(text)
        self.assertEqual(len(result), 1)


class TestMergeSmallChunks(unittest.TestCase):
    """Tests for _merge_small_chunks()."""

    def test_small_chunks_merged(self):
        """Chunks under min_words should be merged."""
        chunks = ["tiny", "also tiny", "still small"]
        merged = _merge_small_chunks(chunks, min_words=10)
        self.assertLess(len(merged), len(chunks))

    def test_large_chunks_not_merged(self):
        """Chunks already over min_words stay separate."""
        large = " ".join([f"word{i}" for i in range(50)])
        chunks = [large, large]
        merged = _merge_small_chunks(chunks, min_words=10)
        self.assertEqual(len(merged), 2)

    def test_empty_list_returns_empty(self):
        """Empty input returns empty list."""
        result = _merge_small_chunks([], min_words=30)
        self.assertEqual(result, [])

    def test_single_chunk_returned(self):
        """Single chunk always returned."""
        chunks = ["just one chunk"]
        merged = _merge_small_chunks(chunks, min_words=5)
        self.assertEqual(len(merged), 1)


class TestHashFile(unittest.TestCase):
    """Tests for _hash_file()."""

    def test_same_content_same_hash(self):
        """Two files with same content produce same hash."""
        fp1 = _write_test_doc("hash_a.txt", "Same content here.")
        fp2 = _write_test_doc("hash_b.txt", "Same content here.")
        self.assertEqual(_hash_file(fp1), _hash_file(fp2))

    def test_different_content_different_hash(self):
        """Different content produces different hash."""
        fp1 = _write_test_doc("diff_a.txt", "Content A here.")
        fp2 = _write_test_doc("diff_b.txt", "Content B here.")
        self.assertNotEqual(_hash_file(fp1), _hash_file(fp2))

    def test_returns_string(self):
        """Hash should be returned as a string."""
        fp     = _write_test_doc("hash_test.txt", "Some content.")
        result = _hash_file(fp)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_missing_file_returns_empty(self):
        """Missing file returns empty string."""
        fp     = Path(TEST_DOCS_DIR) / "nonexistent.txt"
        result = _hash_file(fp)
        self.assertEqual(result, "")


class TestGenerateChunkId(unittest.TestCase):
    """Tests for _generate_chunk_id()."""

    def test_returns_string(self):
        """Should return a string."""
        result = _generate_chunk_id("test.txt", 0, "Some content.")
        self.assertIsInstance(result, str)

    def test_same_inputs_same_id(self):
        """Same inputs always produce same ID."""
        id1 = _generate_chunk_id("guide.txt", 1, "Content here.")
        id2 = _generate_chunk_id("guide.txt", 1, "Content here.")
        self.assertEqual(id1, id2)

    def test_different_index_different_id(self):
        """Different chunk index produces different ID."""
        id1 = _generate_chunk_id("guide.txt", 0, "Same content.")
        id2 = _generate_chunk_id("guide.txt", 1, "Same content.")
        self.assertNotEqual(id1, id2)

    def test_different_file_different_id(self):
        """Different file name produces different ID."""
        id1 = _generate_chunk_id("guide_a.txt", 0, "Content.")
        id2 = _generate_chunk_id("guide_b.txt", 0, "Content.")
        self.assertNotEqual(id1, id2)

    def test_id_contains_file_reference(self):
        """ID should contain a reference to the source file."""
        chunk_id = _generate_chunk_id("vpn_guide.txt", 0, "Content.")
        self.assertIn("vpn_guide", chunk_id)

    def test_no_spaces_in_id(self):
        """Chunk IDs should never contain spaces."""
        chunk_id = _generate_chunk_id("my guide.txt", 0, "Content.")
        self.assertNotIn(" ", chunk_id)


class TestMetadataOperations(unittest.TestCase):
    """Tests for _load_metadata() and _save_metadata()."""

    def setUp(self):
        if os.path.exists(TEST_METADATA):
            os.remove(TEST_METADATA)

    def test_load_returns_empty_when_no_file(self):
        """Loading when no file exists returns empty dict."""
        result = _load_metadata()
        self.assertEqual(result, {})

    def test_save_and_load_roundtrip(self):
        """Saved metadata should be loadable and match original."""
        data = {
            "guide.txt": {
                "hash"        : "abc123",
                "indexed_at"  : "2024-01-01 00:00:00",
                "chunk_count" : 5,
                "file_size"   : 1024,
            }
        }
        _save_metadata(data)
        loaded = _load_metadata()
        self.assertEqual(loaded, data)

    def test_save_overwrites_existing(self):
        """Saving new data should overwrite the old metadata file."""
        _save_metadata({"file_a.txt": {"hash": "old_hash"}})
        _save_metadata({"file_b.txt": {"hash": "new_hash"}})
        loaded = _load_metadata()
        self.assertIn("file_b.txt",    loaded)
        self.assertNotIn("file_a.txt", loaded)


class TestGetChangedFiles(unittest.TestCase):
    """Tests for _get_changed_files()."""

    def setUp(self):
        for f in Path(TEST_DOCS_DIR).glob("*.txt"):
            f.unlink()

    def test_new_file_detected_as_changed(self):
        """A new file not in metadata should be in changed list."""
        fp       = _write_test_doc("new_guide.txt", "Fresh content.")
        changed  = _get_changed_files([fp], metadata={})
        self.assertIn(fp, changed)

    def test_unchanged_file_not_in_changed_list(self):
        """A file whose hash matches metadata should not be changed."""
        fp       = _write_test_doc("existing.txt", "Existing content.")
        metadata = {"existing.txt": {"hash": _hash_file(fp)}}
        changed  = _get_changed_files([fp], metadata=metadata)
        self.assertNotIn(fp, changed)

    def test_modified_file_detected(self):
        """A file with different hash than stored should be changed."""
        fp       = _write_test_doc("modified.txt", "New content after edit.")
        metadata = {"modified.txt": {"hash": "old_stale_hash_value"}}
        changed  = _get_changed_files([fp], metadata=metadata)
        self.assertIn(fp, changed)

    def test_empty_docs_returns_empty(self):
        """No files means no changed files."""
        changed = _get_changed_files([], metadata={})
        self.assertEqual(changed, [])


class TestCleanQuery(unittest.TestCase):
    """Tests for _clean_query()."""

    def test_lowercases_query(self):
        """Query should be lowercased."""
        result = _clean_query("INSTALL ZOOM ON MY LAPTOP")
        self.assertEqual(result, result.lower())

    def test_removes_email_addresses(self):
        """Email addresses should be stripped from query."""
        result = _clean_query("Contact rahul@icici.com for help")
        self.assertNotIn("rahul@icici.com", result)

    def test_removes_machine_names(self):
        """Machine names like PC-ICICI-0042 should be removed."""
        result = _clean_query("Install on PC-ICICI-0042 machine")
        self.assertNotIn("PC-ICICI-0042", result)

    def test_expands_av_abbreviation(self):
        """'av' should expand to 'antivirus'."""
        result = _clean_query("av not working on my laptop")
        self.assertIn("antivirus", result)

    def test_expands_vpn_abbreviation(self):
        """'vpn' should be expanded."""
        result = _clean_query("vpn not connecting")
        self.assertIn("vpn", result)

    def test_empty_query_returns_empty(self):
        """Empty query returns empty string."""
        result = _clean_query("")
        self.assertEqual(result, "")

    def test_very_long_query_trimmed(self):
        """
        Queries over 200 words should be trimmed to
        prevent embedding quality issues.
        """
        long_query = "help me " * 300
        result     = _clean_query(long_query)
        word_count = len(result.split())
        self.assertLessEqual(word_count, 205)

    def test_special_chars_removed(self):
        """Special characters should be replaced with spaces."""
        result = _clean_query("zoom!!! not@working #urgent")
        self.assertNotIn("!!!", result)
        self.assertNotIn("@",   result)
        self.assertNotIn("#",   result)

    def test_normalizes_whitespace(self):
        """Multiple spaces should be collapsed to one."""
        result = _clean_query("install    zoom    on   laptop")
        self.assertNotIn("  ", result)


class TestFilterByScore(unittest.TestCase):
    """Tests for _filter_by_score()."""

    def _make_results(self, scores):
        return [
            {
                "text"        : f"Content {s}",
                "score"       : s,
                "file_name"   : "test.txt",
                "chunk_index" : i,
                "word_count"  : 50,
                "indexed_at"  : "",
                "id"          : f"id_{i}",
            }
            for i, s in enumerate(scores)
        ]

    def test_filters_below_threshold(self):
        """Results below min_score should be excluded."""
        results  = self._make_results([0.8, 0.5, 0.2, 0.1])
        filtered = _filter_by_score(results, min_score=0.4)
        scores   = [r["score"] for r in filtered]
        self.assertNotIn(0.2, scores)
        self.assertNotIn(0.1, scores)

    def test_keeps_above_threshold(self):
        """Results above min_score should be kept."""
        results  = self._make_results([0.9, 0.7, 0.5])
        filtered = _filter_by_score(results, min_score=0.4)
        self.assertEqual(len(filtered), 3)

    def test_empty_results_returns_empty(self):
        """Empty input returns empty list."""
        filtered = _filter_by_score([], min_score=0.3)
        self.assertEqual(filtered, [])

    def test_all_below_threshold_returns_empty(self):
        """If all results below threshold, return empty list."""
        results  = self._make_results([0.1, 0.05, 0.02])
        filtered = _filter_by_score(results, min_score=0.3)
        self.assertEqual(filtered, [])

    def test_exact_threshold_score_kept(self):
        """Result with score exactly at threshold should be kept."""
        results  = self._make_results([0.30])
        filtered = _filter_by_score(results, min_score=0.30)
        self.assertEqual(len(filtered), 1)


class TestDeduplicateResults(unittest.TestCase):
    """Tests for _deduplicate_results()."""

    def _make_result(self, text, file_name, score=0.8, idx=0):
        return {
            "text"        : text,
            "score"       : score,
            "file_name"   : file_name,
            "chunk_index" : idx,
            "word_count"  : len(text.split()),
            "indexed_at"  : "",
            "id"          : f"{file_name}_{idx}",
        }

    def test_empty_input_returns_empty(self):
        """Empty list input returns empty list."""
        result = _deduplicate_results([])
        self.assertEqual(result, [])

    def test_single_result_preserved(self):
        """Single result should always be returned."""
        results = [self._make_result("Some guide text here.", "guide.txt")]
        deduped = _deduplicate_results(results)
        self.assertEqual(len(deduped), 1)

    def test_max_two_chunks_per_file(self):
        """At most 2 chunks from the same file should be kept."""
        results = [
            self._make_result(f"Unique content chunk {i}", "guide.txt", idx=i)
            for i in range(5)
        ]
        deduped = _deduplicate_results(results)
        count   = sum(1 for r in deduped if r["file_name"] == "guide.txt")
        self.assertLessEqual(count, 2)

    def test_different_files_both_kept(self):
        """Results from different files should both be kept."""
        results = [
            self._make_result("VPN guide content here.", "vpn.txt"),
            self._make_result("Printer guide content.",  "printer.txt"),
        ]
        deduped = _deduplicate_results(results)
        self.assertEqual(len(deduped), 2)

    def test_near_duplicate_removed(self):
        """Near-duplicate chunks (>60% overlap) should be deduplicated."""
        base_text = "How to reset your password in Windows domain account"
        dup_text  = "How to reset your password in Windows domain account today"

        results = [
            self._make_result(base_text, "guide.txt", idx=0),
            self._make_result(dup_text,  "guide.txt", idx=1),
        ]
        deduped = _deduplicate_results(results)
        self.assertLessEqual(len(deduped), 2)


class TestTextOverlapRatio(unittest.TestCase):
    """Tests for _text_overlap_ratio()."""

    def test_identical_texts_give_one(self):
        """Identical texts should give overlap ratio of 1.0."""
        text   = "the quick brown fox jumps over the lazy dog"
        result = _text_overlap_ratio(text, text)
        self.assertAlmostEqual(result, 1.0, places=2)

    def test_completely_different_gives_zero(self):
        """Completely different texts should give low overlap."""
        text_a = "vpn network connection internet router firewall"
        text_b = "password forgot locked account windows login"
        result = _text_overlap_ratio(text_a, text_b)
        self.assertLess(result, 0.2)

    def test_empty_text_a_gives_zero(self):
        """Empty text_a should give 0.0 ratio."""
        result = _text_overlap_ratio("", "some content")
        self.assertEqual(result, 0.0)

    def test_ratio_between_zero_and_one(self):
        """Overlap ratio should always be between 0.0 and 1.0."""
        text_a = "install zoom on laptop using sccm"
        text_b = "install teams on laptop using intune"
        result = _text_overlap_ratio(text_a, text_b)
        self.assertGreaterEqual(result, 0.0)
        self.assertLessEqual(result, 1.0)

    def test_partial_overlap(self):
        """Texts sharing some words should have intermediate ratio."""
        text_a = "cannot connect to vpn from home network"
        text_b = "cannot connect to internet from office network"
        result = _text_overlap_ratio(text_a, text_b)
        self.assertGreater(result, 0.0)
        self.assertLess(result, 1.0)


class TestFormatGuide(unittest.TestCase):
    """Tests for _format_guide()."""

    def _make_result(self, text, file_name, score=0.8):
        return {
            "text"        : text,
            "score"       : score,
            "file_name"   : file_name,
            "chunk_index" : 0,
            "word_count"  : len(text.split()),
            "indexed_at"  : "",
            "id"          : f"{file_name}_0",
        }

    def test_returns_string(self):
        """Format guide should return a string."""
        results = [
            self._make_result("Step 1 open VPN client.", "vpn_guide.txt")
        ]
        output = _format_guide(results, "vpn not working")
        self.assertIsInstance(output, str)

    def test_contains_guide_content(self):
        """Output should contain the chunk text."""
        results = [
            self._make_result("Step 1 open the application.", "guide.txt")
        ]
        output = _format_guide(results, "how to open app")
        self.assertIn("Step 1 open the application.", output)

    def test_contains_footer(self):
        """Output should contain the standard footer text."""
        results = [
            self._make_result("Some guide content.", "guide.txt")
        ]
        output = _format_guide(results, "query")
        self.assertIn("Knowledge Base", output)

    def test_empty_results_returns_empty(self):
        """Empty results list should return empty string."""
        output = _format_guide([], "any query")
        self.assertEqual(output, "")

    def test_multi_source_has_section_headers(self):
        """Multiple source files should produce section headers."""
        results = [
            self._make_result("VPN steps here.",     "vpn_guide.txt"),
            self._make_result("Outlook steps here.", "outlook_guide.txt"),
        ]
        output = _format_guide(results, "vpn and outlook")
        self.assertGreater(len(output), 50)


class TestFileNameToTitle(unittest.TestCase):
    """Tests for _file_name_to_title()."""

    def test_underscores_replaced_with_spaces(self):
        """Underscores in filename should become spaces."""
        result = _file_name_to_title("vpn_setup_guide.txt")
        self.assertNotIn("_", result)

    def test_extension_removed(self):
        """File extension should be stripped from title."""
        result = _file_name_to_title("printer_guide.txt")
        self.assertNotIn(".txt", result)

    def test_capitalized_words(self):
        """Each word in title should start with capital letter."""
        result = _file_name_to_title("password_reset_guide.txt")
        for word in result.split():
            self.assertTrue(
                word[0].isupper(),
                f"Word '{word}' not capitalized in '{result}'"
            )

    def test_vpn_override_applied(self):
        """VPN should be uppercase in override list."""
        result = _file_name_to_title("vpn_setup_guide.txt")
        self.assertIn("VPN", result)

    def test_md_extension_stripped(self):
        """Markdown extension should also be stripped."""
        result = _file_name_to_title("some_guide.md")
        self.assertNotIn(".md", result)


class TestScoreToLabel(unittest.TestCase):
    """Tests for _score_to_label()."""

    def test_high_score_label(self):
        """Score >= 0.75 should return 'High' label."""
        result = _score_to_label(0.80)
        self.assertIn("High", result)

    def test_medium_score_label(self):
        """Score between 0.50 and 0.75 should return 'Medium'."""
        result = _score_to_label(0.60)
        self.assertIn("Medium", result)

    def test_low_score_label(self):
        """Score between 0.30 and 0.50 should return 'Low'."""
        result = _score_to_label(0.35)
        self.assertIn("Low", result)

    def test_very_low_score_label(self):
        """Score below 0.30 should return 'Very Low'."""
        result = _score_to_label(0.15)
        self.assertIn("Very Low", result)

    def test_score_percentage_included(self):
        """Result should include the percentage."""
        result = _score_to_label(0.75)
        self.assertIn("%", result)

    def test_returns_string(self):
        """Should always return a string."""
        for score in [0.0, 0.3, 0.5, 0.75, 1.0]:
            self.assertIsInstance(_score_to_label(score), str)


class TestCleanChunkText(unittest.TestCase):
    """Tests for _clean_chunk_text()."""

    def test_strips_leading_trailing_whitespace(self):
        """Should strip leading and trailing whitespace."""
        result = _clean_chunk_text("  Content here.  ")
        self.assertEqual(result, "Content here.")

    def test_normalizes_multiple_newlines(self):
        """Three or more newlines should be reduced to two."""
        result = _clean_chunk_text("Line 1.\n\n\n\nLine 2.")
        self.assertNotIn("\n\n\n", result)

    def test_empty_returns_empty(self):
        """Empty input returns empty string."""
        result = _clean_chunk_text("")
        self.assertEqual(result, "")

    def test_content_preserved(self):
        """Main content should be preserved after cleaning."""
        content = "Step 1: Open the application and click Connect."
        result  = _clean_chunk_text(content)
        self.assertIn("Step 1:", result)
        self.assertIn("click Connect", result)


class TestSearchKnowledgeBase(unittest.TestCase):
    """
    Integration-style tests for search_knowledge_base().
    Uses mocked ChromaDB so no real embeddings are needed.
    """

    def _make_mock_collection(self, docs, scores):
        """Build a mock ChromaDB collection query response."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = len(docs)

        distances = [1.0 - s for s in scores]

        mock_collection.query.return_value = {
            "documents": [docs],
            "metadatas": [
                [
                    {
                        "file_name"   : "vpn_guide.txt",
                        "chunk_index" : i,
                        "word_count"  : len(d.split()),
                        "indexed_at"  : "2024-01-01 00:00:00",
                    }
                    for i, d in enumerate(docs)
                ]
            ],
            "distances": [distances],
            "ids"       : [[f"chunk_{i}" for i in range(len(docs))]],
        }
        return mock_collection

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_string_when_results_found(self, mock_get_col):
        """Should return a string when relevant results are found."""
        docs = [
            "Step 1: Open Cisco AnyConnect from Start menu.",
            "Step 2: Enter vpn.company.com in the server box.",
        ]
        mock_get_col.return_value = self._make_mock_collection(
            docs, [0.85, 0.75]
        )

        result = search_knowledge_base(
            "cannot connect to vpn from home"
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 20)

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_none_when_score_too_low(self, mock_get_col):
        """
        Should return None when all results score below
        the minimum threshold.
        """
        docs = ["Some unrelated content about databases."]
        mock_get_col.return_value = self._make_mock_collection(
            docs, [0.05]
        )

        result = search_knowledge_base(
            "install zoom on my laptop"
        )

        self.assertIsNone(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_empty_query_returns_none(self, mock_get_col):
        """Empty query should return None without querying ChromaDB."""
        result = search_knowledge_base("")
        self.assertIsNone(result)
        mock_get_col.assert_not_called()

    @patch("knowledge_base.kb_search._get_collection")
    def test_whitespace_query_returns_none(self, mock_get_col):
        """Whitespace-only query should return None."""
        result = search_knowledge_base("   ")
        self.assertIsNone(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_collection_unavailable_returns_none(self, mock_get_col):
        """When ChromaDB is unavailable, should return None."""
        mock_get_col.return_value = None

        result = search_knowledge_base("vpn not working")
        self.assertIsNone(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_result_contains_guide_content(self, mock_get_col):
        """Returned guide should contain the retrieved chunk text."""
        docs = ["Open AnyConnect and enter vpn.company.com to connect."]
        mock_get_col.return_value = self._make_mock_collection(
            docs, [0.90]
        )

        result = search_knowledge_base("how to connect vpn")

        self.assertIsNotNone(result)
        self.assertIn("AnyConnect", result)


class TestSearchByCategory(unittest.TestCase):
    """Tests for search_by_category()."""

    @patch("knowledge_base.kb_search.search_knowledge_base")
    def test_all_categories_trigger_search(self, mock_search):
        """Each category should trigger a search call."""
        mock_search.return_value = "Some guide content."

        categories = [
            "app_install", "antivirus", "password_reset",
            "network", "printer", "email_issue",
        ]

        for cat in categories:
            result = search_by_category(cat)
            self.assertIsNotNone(result)

        self.assertGreater(mock_search.call_count, 0)

    @patch("knowledge_base.kb_search.search_knowledge_base")
    def test_unknown_category_still_searches(self, mock_search):
        """Unknown category should still attempt a search."""
        mock_search.return_value = None
        result = search_by_category("unknown_category_xyz")
        mock_search.assert_called_once()

    @patch("knowledge_base.kb_search.search_knowledge_base")
    def test_returns_none_when_no_guide_found(self, mock_search):
        """Should return None if search finds nothing."""
        mock_search.return_value = None
        result = search_by_category("hardware")
        self.assertIsNone(result)


class TestSearchMultiQuery(unittest.TestCase):
    """Tests for search_multi_query()."""

    @patch("knowledge_base.kb_search._vector_search")
    @patch("knowledge_base.kb_search._get_collection")
    def test_empty_queries_returns_none(self, mock_col, mock_search):
        """Empty query list returns None."""
        result = search_multi_query([])
        self.assertIsNone(result)

    @patch("knowledge_base.kb_search.search_knowledge_base")
    def test_single_query_in_list(self, mock_search):
        """Single query list should work the same as one query."""
        mock_search.return_value = "Guide content here."
        result = search_multi_query(["vpn not connecting"])
        mock_search.assert_not_called()

    def test_whitespace_queries_skipped(self):
        """Whitespace-only queries should be skipped."""
        result = search_multi_query(["  ", "", "   "])
        self.assertIsNone(result)


class TestIsKbAvailable(unittest.TestCase):
    """Tests for is_kb_available()."""

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_true_when_collection_has_docs(self, mock_get_col):
        """Should return True when collection has documents."""
        mock_col = MagicMock()
        mock_col.count.return_value = 25
        mock_get_col.return_value   = mock_col

        result = is_kb_available()
        self.assertTrue(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_false_when_collection_empty(self, mock_get_col):
        """Should return False when collection has 0 documents."""
        mock_col = MagicMock()
        mock_col.count.return_value = 0
        mock_get_col.return_value   = mock_col

        result = is_kb_available()
        self.assertFalse(result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_false_when_collection_none(self, mock_get_col):
        """Should return False when collection is None."""
        mock_get_col.return_value = None

        result = is_kb_available()
        self.assertFalse(result)


class TestGetKbStats(unittest.TestCase):
    """Tests for get_kb_stats()."""

    @patch("knowledge_base.kb_search._get_collection")
    def test_returns_dict(self, mock_get_col):
        """Should always return a dict."""
        mock_col = MagicMock()
        mock_col.count.return_value = 50
        mock_get_col.return_value   = mock_col

        result = get_kb_stats()
        self.assertIsInstance(result, dict)

    @patch("knowledge_base.kb_search._get_collection")
    def test_stats_has_required_keys(self, mock_get_col):
        """Stats dict should have all required keys."""
        mock_col = MagicMock()
        mock_col.count.return_value = 50
        mock_get_col.return_value   = mock_col

        result = get_kb_stats()

        required_keys = [
            "is_available",
            "total_chunks",
            "collection_name",
            "chroma_dir",
            "embed_model",
        ]
        for key in required_keys:
            self.assertIn(key, result)

    @patch("knowledge_base.kb_search._get_collection")
    def test_unavailable_stats(self, mock_get_col):
        """When collection unavailable, is_available should be False."""
        mock_get_col.return_value = None

        result = get_kb_stats()
        self.assertFalse(result["is_available"])
        self.assertEqual(result["total_chunks"], 0)


def run_all_tests():
    """Run the complete KB test suite."""
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    test_classes = [
        TestScanDocsFolder,
        TestLoadDocument,
        TestChunkText,
        TestSplitIntoSentences,
        TestMergeSmallChunks,
        TestHashFile,
        TestGenerateChunkId,
        TestMetadataOperations,
        TestGetChangedFiles,
        TestCleanQuery,
        TestFilterByScore,
        TestDeduplicateResults,
        TestTextOverlapRatio,
        TestFormatGuide,
        TestFileNameToTitle,
        TestScoreToLabel,
        TestCleanChunkText,
        TestSearchKnowledgeBase,
        TestSearchByCategory,
        TestSearchMultiQuery,
        TestIsKbAvailable,
        TestGetKbStats,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)

    print("\n" + "=" * 65)
    print("KNOWLEDGE BASE TEST SUITE")
    print("=" * 65 + "\n")

    result = runner.run(suite)

    _cleanup_test_dir()

    print("\n" + "=" * 65)
    print("TEST SUMMARY")
    print("=" * 65)
    print(f"  Tests run : {result.testsRun}")
    print(f"  Passed    : {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failures  : {len(result.failures)}")
    print(f"  Errors    : {len(result.errors)}")
    print(f"  Overall   : {'PASSED' if result.wasSuccessful() else 'FAILED'}")
    print("=" * 65 + "\n")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)