#!/usr/bin/env python3
"""
Unit tests for DocuSearch components
"""

import pytest

from docusearch import DocumentStorage
from docusearch.trie import Trie


class TestTrie:
    """Unit tests for Trie data structure"""

    def test_trie_insert_and_search(self):
        """Test basic trie insertion and search functionality"""
        trie = Trie()

        # Insert words
        trie.insert("python")
        trie.insert("programming")

        # Test exact search
        assert trie.search("python") is True
        assert trie.search("programming") is True
        assert trie.search("nonexistent") is False

        # Test prefix search
        assert "python" in trie.starts_with("py")
        assert "programming" in trie.starts_with("prog")
        assert trie.starts_with("xyz") == []

    def test_trie_word_counts(self):
        """Test word count tracking in trie"""
        trie = Trie()

        trie.insert("python")
        trie.add_document_to_word("python", "doc1", 2)
        trie.add_document_to_word("python", "doc2", 1)

        # Get word info
        docs = trie.get_documents_for_word("python")
        assert docs["doc1"] == 2
        assert docs["doc2"] == 1

    def test_trie_delete_word(self):
        """Test deleting words from trie"""
        trie = Trie()

        trie.insert("python")
        trie.add_document_to_word("python", "doc1", 1)
        trie.add_document_to_word("python", "doc2", 1)
        trie.insert("programming")
        trie.add_document_to_word("programming", "doc1", 1)

        # Delete word from specific document
        trie.remove_document_from_word("python", "doc1")
        docs = trie.get_documents_for_word("python")
        assert "doc1" not in docs
        assert "doc2" in docs

        # Delete word completely
        trie.remove_document_from_word("python", "doc2")
        docs = trie.get_documents_for_word("python")
        assert len(docs) == 0

    def test_trie_empty_operations(self):
        """Test trie operations on empty trie"""
        trie = Trie()

        assert trie.search("any") is False
        assert trie.starts_with("any") == []
        assert trie.get_documents_for_word("any") == {}


class TestDocumentStorage:
    """Unit tests for DocumentStorage class"""

    @pytest.fixture
    def storage(self):
        """Create a fresh DocumentStorage instance for each test"""
        return DocumentStorage()

    def test_add_document(self, storage):
        """Test adding a document with text content"""
        doc_id = storage.add_document("This is a test document.", "test_doc")

        assert doc_id == "test_doc"
        doc_info = storage.get_document_info(doc_id)
        assert doc_info is not None
        assert doc_info["content"] == "This is a test document."

    def test_add_document_auto_id(self, storage):
        """Test adding a document with auto-generated ID"""
        doc_id = storage.add_document("Another test document.")

        assert doc_id is not None
        doc_info = storage.get_document_info(doc_id)
        assert doc_info is not None
        assert doc_info["content"] == "Another test document."

    def test_delete_document(self, storage):
        """Test deleting a document"""
        doc_id = storage.add_document("Test document to delete.", "delete_test")

        # Verify document exists
        doc_info = storage.get_document_info(doc_id)
        assert doc_info is not None

        # Delete document
        result = storage.remove_document(doc_id)

        # Verify document is removed
        assert result is True
        doc_info_after = storage.get_document_info(doc_id)
        assert doc_info_after is None
        stats = storage.get_stats()
        assert stats["total_documents"] == 0

    def test_delete_nonexistent_document(self, storage):
        """Test deleting a document that doesn't exist"""
        # Should not raise an exception
        result = storage.remove_document("nonexistent")
        assert result is False
        stats = storage.get_stats()
        assert stats["total_documents"] == 0

    def test_get_document_info(self, storage):
        """Test getting document information"""
        storage.add_document(
            "This is a test document with multiple words.", "info_test"
        )

        info = storage.get_document_info("info_test")

        assert info is not None
        assert info["total_words"] == 7  # "This is a test document with multiple words"
        assert info["unique_words"] == 7
        assert "content" in info

    def test_get_nonexistent_document_info(self, storage):
        """Test getting info for nonexistent document"""
        info = storage.get_document_info("nonexistent")
        assert info is None

    def test_get_stats_empty(self, storage):
        """Test getting stats for empty storage"""
        stats = storage.get_stats()

        assert stats["total_documents"] == 0
        assert stats["total_words"] == 0

    def test_get_stats_with_documents(self, storage):
        """Test getting stats with documents"""
        storage.add_document("First document.", "doc1")
        storage.add_document("Second document with more words.", "doc2")

        stats = storage.get_stats()

        assert stats["total_documents"] == 2
        assert stats["total_words"] > 0

    def test_search_empty_storage(self, storage):
        """Test search on empty storage"""
        results = storage.search("test")
        assert results == []

    def test_search_single_document(self, storage):
        """Test search with single document"""
        storage.add_document("This document contains python programming.", "python_doc")

        results = storage.search("python")

        assert len(results) == 1
        assert results[0][0] == "python_doc"
        assert results[0][1] > 0  # Score should be positive

    def test_search_multiple_documents(self, storage):
        """Test search with multiple documents"""
        storage.add_document("Python programming language.", "doc1")
        storage.add_document("Java programming language.", "doc2")
        storage.add_document("Web development with HTML.", "doc3")

        results = storage.search("programming")

        assert len(results) == 2
        doc_ids = [result[0] for result in results]
        assert "doc1" in doc_ids
        assert "doc2" in doc_ids

    def test_prefix_search_empty(self, storage):
        """Test prefix search on empty storage"""
        words = storage.prefix_search("test")
        assert words == []

    def test_prefix_search_with_documents(self, storage):
        """Test prefix search with documents"""
        storage.add_document("Python programming.", "doc1")
        storage.add_document("Java programming.", "doc2")
        storage.add_document("JavaScript programming.", "doc3")

        words = storage.prefix_search("prog")
        assert "programming" in words

    def test_add_document_from_path_nonexistent(self, storage):
        """Test adding document from nonexistent path"""
        with pytest.raises(FileNotFoundError):
            storage.add_document_from_path("nonexistent_file.txt")

    def test_tfidf_scoring(self, storage):
        """Test TF-IDF scoring calculations"""
        # Add documents with known word frequencies
        storage.add_document("python python python", "doc1")  # 3 occurrences
        storage.add_document("python java", "doc2")  # 1 occurrence
        storage.add_document("java java", "doc3")  # 0 occurrences of python

        results = storage.search("python")

        # doc1 should have higher score than doc2 due to higher TF
        assert len(results) == 2
        doc1_score = next(score for doc_id, score, _ in results if doc_id == "doc1")
        doc2_score = next(score for doc_id, score, _ in results if doc_id == "doc2")
        assert doc1_score > doc2_score

    def test_search_top_k_limit(self, storage):
        """Test that search respects top_k parameter"""
        storage.add_document("python programming", "doc1")
        storage.add_document("python development", "doc2")
        storage.add_document("python scripting", "doc3")

        results = storage.search("python", top_k=2)
        assert len(results) == 2

    def test_search_case_insensitive(self, storage):
        """Test that search is case insensitive"""
        storage.add_document("Python Programming", "doc1")

        results_lower = storage.search("python")
        results_upper = storage.search("PYTHON")
        results_mixed = storage.search("Python")

        assert len(results_lower) == 1
        assert len(results_upper) == 1
        assert len(results_mixed) == 1
        assert results_lower[0][0] == results_upper[0][0] == results_mixed[0][0]


class TestCLI:
    """Unit tests for CLI functionality"""

    def test_cli_import(self):
        """Test that CLI can be imported"""
        from docusearch.cli import main, repl

        assert callable(main)
        assert callable(repl)
