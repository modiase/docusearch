#!/usr/bin/env python3
"""
Shared pytest fixtures for DocuSearch tests
"""

import pytest

from docusearch import DocumentStorage


@pytest.fixture
def storage():
    """Create a fresh DocumentStorage instance for each test"""
    return DocumentStorage()


@pytest.fixture
def sample_documents():
    """Sample document content for testing"""
    return {
        "doc1": "Python is a programming language used for web development and data science.",
        "doc2": "Machine learning algorithms are used in artificial intelligence applications.",
        "doc3": "Web development involves HTML, CSS, JavaScript and various frameworks.",
        "doc4": "Data science combines statistics, programming, and domain expertise.",
    }


@pytest.fixture
def populated_storage(storage, sample_documents):
    """Create a DocumentStorage instance with sample documents"""
    for doc_id, content in sample_documents.items():
        storage.add_document(content, doc_id)
    return storage
