#!/usr/bin/env python3
"""
Demonstration script for DocuSearch
"""

import os

from docusearch import DocumentStorage


def main():
    print("DocuSearch Demonstration")
    print("=" * 50)

    # Create storage instance
    storage = DocumentStorage()

    # Add sample documents
    print("\n1. Adding sample documents...")

    # Add documents from examples directory
    example_files = [
        "examples/sample_documents.txt",
        "examples/machine_learning.txt",
        "examples/web_development.txt",
    ]

    for file_path in example_files:
        if os.path.exists(file_path):
            doc_id = storage.add_document_from_path(file_path)
            print(f"   Added: {file_path} -> {doc_id}")
        else:
            print(f"   Warning: {file_path} not found")

    # Add a custom document
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

    # Demonstrate prefix search
    print("\n4. Prefix Search Examples:")

    prefixes = ["prog", "mach", "web", "data"]

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


if __name__ == "__main__":
    main()
