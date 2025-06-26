#!/usr/bin/env python3
"""
Integration tests for DocuSearch
"""

import pytest

from docusearch import DocumentStorage


class TestDocumentStorageIntegration:
    """Integration tests for DocumentStorage functionality"""

    @pytest.fixture
    def storage(self):
        """Create a fresh DocumentStorage instance for each test"""
        return DocumentStorage()

    @pytest.fixture
    def sample_files(self, tmp_path):
        """Create sample files for testing"""
        # Create sample documents
        sample_docs = {
            "sample_documents.txt": "Python is a programming language. Python is used for web development and data science.",
            "machine_learning.txt": "Machine learning algorithms are used in artificial intelligence. Deep learning is a subset of machine learning.",
            "web_development.txt": "Web development involves HTML, CSS, and JavaScript. Frameworks like React and Django are popular.",
        }

        files = {}
        for filename, content in sample_docs.items():
            file_path = tmp_path / filename
            file_path.write_text(content)
            files[filename] = str(file_path)

        return files

    def test_add_documents_from_files(self, storage, sample_files, capsys):
        """Test adding documents from file paths"""
        print("1. Adding sample documents...")

        for file_path in sample_files.values():
            doc_id = storage.add_document_from_path(file_path)
            print(f"   Added: {file_path} -> {doc_id}")

        captured = capsys.readouterr()
        assert "Adding sample documents..." in captured.out
        assert "Added:" in captured.out
        assert len(storage.documents) == 3

    def test_add_custom_document(self, storage, capsys):
        """Test adding a custom document with text content"""
        print("   Added: Custom document -> data_science_doc")

        custom_doc_id = storage.add_document(
            "Data science is an interdisciplinary field that uses scientific methods, processes, algorithms and systems to extract knowledge and insights from structured and unstructured data.",
            "data_science_doc",
        )

        captured = capsys.readouterr()
        assert "Custom document -> data_science_doc" in captured.out
        assert custom_doc_id == "data_science_doc"
        assert custom_doc_id in storage.documents

    def test_storage_statistics(self, storage, sample_files, capsys):
        """Test storage statistics output"""
        # Add documents first
        for file_path in sample_files.values():
            storage.add_document_from_path(file_path)

        print("2. Storage Statistics:")
        stats = storage.get_stats()
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Total unique words: {stats['total_words']}")

        captured = capsys.readouterr()
        assert "Storage Statistics:" in captured.out
        assert f"Total documents: {stats['total_documents']}" in captured.out
        assert f"Total unique words: {stats['total_words']}" in captured.out
        assert stats["total_documents"] == 3
        assert stats["total_words"] > 0

    def test_tfidf_search_examples(self, storage, sample_files, capsys):
        """Test TF-IDF search functionality with various queries"""
        # Add documents first
        for file_path in sample_files.values():
            storage.add_document_from_path(file_path)

        print("3. TF-IDF Search Examples:")

        queries = [
            "python programming",
            "machine learning algorithms",
            "web development frameworks",
            "data science",
        ]

        for query in queries:
            print(f"\n   Query: '{query}'")
            results = storage.search(query, top_k=3)

            if results:
                for i, (doc_id, score, preview) in enumerate(results, 1):
                    print(f"   {i}. {doc_id} (score: {score:.4f})")
                    print(f"      Preview: {preview[:100]}...")
            else:
                print("   No results found")

        captured = capsys.readouterr()
        assert "TF-IDF Search Examples:" in captured.out
        assert "Query: 'python programming'" in captured.out
        assert "Query: 'machine learning algorithms'" in captured.out
        assert "Query: 'web development frameworks'" in captured.out
        assert "Query: 'data science'" in captured.out

    def test_prefix_search_examples(self, storage, sample_files, capsys):
        """Test prefix search functionality"""
        # Add documents first
        for file_path in sample_files.values():
            storage.add_document_from_path(file_path)

        print("4. Prefix Search Examples:")

        prefixes = ["prog", "mach", "web", "data"]

        for prefix in prefixes:
            words = storage.prefix_search(prefix)
            print(f"   Words starting with '{prefix}': {sorted(words)}")

        captured = capsys.readouterr()
        assert "Prefix Search Examples:" in captured.out
        assert "Words starting with 'prog':" in captured.out
        assert "Words starting with 'mach':" in captured.out
        assert "Words starting with 'web':" in captured.out
        assert "Words starting with 'data':" in captured.out

    def test_document_details(self, storage, sample_files, capsys):
        """Test document information display"""
        # Add documents first
        for file_path in sample_files.values():
            storage.add_document_from_path(file_path)

        print("5. Document Details:")
        for doc_id in storage.documents.keys():
            info = storage.get_document_info(doc_id)
            if info:
                print(
                    f"   {doc_id}: {info['total_words']} words, {info['unique_words']} unique words"
                )

        captured = capsys.readouterr()
        assert "Document Details:" in captured.out
        assert "words, " in captured.out
        assert "unique words" in captured.out

    def test_full_demonstration_flow(self, storage, sample_files, capsys):
        """Test the complete demonstration flow"""
        print("DocuSearch Demonstration")
        print("=" * 50)

        # Add documents
        print("\n1. Adding sample documents...")
        for file_path in sample_files.values():
            doc_id = storage.add_document_from_path(file_path)
            print(f"   Added: {file_path} -> {doc_id}")

        # Add custom document
        custom_doc_id = storage.add_document(
            "Data science is an interdisciplinary field that uses scientific methods, processes, algorithms and systems to extract knowledge and insights from structured and unstructured data.",
            "data_science_doc",
        )
        print(f"   Added: Custom document -> {custom_doc_id}")

        # Show statistics
        print("\n2. Storage Statistics:")
        stats = storage.get_stats()
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Total unique words: {stats['total_words']}")

        # Demonstrate search
        print("\n3. TF-IDF Search Examples:")
        queries = ["python programming", "machine learning algorithms"]
        for query in queries:
            print(f"\n   Query: '{query}'")
            results = storage.search(query, top_k=2)
            if results:
                for i, (doc_id, score, preview) in enumerate(results, 1):
                    print(f"   {i}. {doc_id} (score: {score:.4f})")
                    print(f"      Preview: {preview[:100]}...")

        # Demonstrate prefix search
        print("\n4. Prefix Search Examples:")
        prefixes = ["prog", "mach"]
        for prefix in prefixes:
            words = storage.prefix_search(prefix)
            print(f"   Words starting with '{prefix}': {sorted(words)}")

        # Show document details
        print("\n5. Document Details:")
        for doc_id in storage.documents.keys():
            info = storage.get_document_info(doc_id)
            if info:
                print(
                    f"   {doc_id}: {info['total_words']} words, {info['unique_words']} unique words"
                )

        print("\n" + "=" * 50)
        print("Demonstration completed!")

        captured = capsys.readouterr()
        output = captured.out

        # Verify all major sections are present
        assert "DocuSearch Demonstration" in output
        assert "Adding sample documents..." in output
        assert "Storage Statistics:" in output
        assert "TF-IDF Search Examples:" in output
        assert "Prefix Search Examples:" in output
        assert "Document Details:" in output
        assert "Demonstration completed!" in output

        # Verify document operations worked
        assert len(storage.documents) == 4  # 3 files + 1 custom
        assert "data_science_doc" in storage.documents

    def test_search_with_no_results(self, storage, capsys):
        """Test search behavior when no results are found"""
        print("   Query: 'nonexistent term'")
        results = storage.search("nonexistent term", top_k=3)
        print("   No results found")

        captured = capsys.readouterr()
        assert "Query: 'nonexistent term'" in captured.out
        assert "No results found" in captured.out
        assert results == []

    def test_prefix_search_with_no_matches(self, storage, capsys):
        """Test prefix search when no words match"""
        print("   Words starting with 'xyz': []")
        words = storage.prefix_search("xyz")
        print(f"   Words starting with 'xyz': {sorted(words)}")

        captured = capsys.readouterr()
        assert "Words starting with 'xyz':" in captured.out
        assert words == []

    def test_document_deletion(self, storage, sample_files, capsys):
        """Test document deletion functionality"""
        # Add a document
        file_path = list(sample_files.values())[0]
        doc_ids = storage.add_document_from_path(file_path)
        doc_id = doc_ids[0]  # Get the first (and only) document ID
        print(f"   Added: {file_path} -> {doc_id}")

        # Delete the document
        result = storage.remove_document(doc_id)
        print(f"   Deleted: {doc_id}")

        captured = capsys.readouterr()
        assert "Added:" in captured.out
        assert "Deleted:" in captured.out
        assert result is True
        assert doc_id not in storage.documents
        assert len(storage.documents) == 0
