#!/usr/bin/env python3
"""
DocuSearch - In-memory document storage with TF-IDF search
"""

from docusearch import DocumentStorage


def main():
    print("DocuSearch - In-memory Document Storage Library")
    print("=" * 50)

    # Create storage instance
    storage = DocumentStorage()

    # Add some sample documents
    print("\nAdding sample documents...")

    doc1_id = storage.add_document(
        "Python is a high-level programming language known for its simplicity and readability.",
        "python_doc",
    )

    doc2_id = storage.add_document(
        "Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
        "ml_doc",
    )

    doc3_id = storage.add_document(
        "Web development involves creating websites and web applications using various technologies.",
        "web_doc",
    )

    print(f"Added documents: {doc1_id}, {doc2_id}, {doc3_id}")

    # Demonstrate search
    print("\nSearching for 'python programming'...")
    results = storage.search("python programming", top_k=3)

    for i, (doc_id, score, preview) in enumerate(results, 1):
        print(f"{i}. {doc_id} (score: {score:.4f})")
        print(f"   Preview: {preview}")

    # Demonstrate prefix search
    print("\nPrefix search for 'prog'...")
    words = storage.prefix_search("prog")
    print(f"Words starting with 'prog': {words}")

    # Show statistics
    print("\nStorage Statistics:")
    stats = storage.get_stats()
    print(f"Total documents: {stats['total_documents']}")
    print(f"Total unique words: {stats['total_words']}")

    print("\nFor more features, use the CLI: docusearch --help")


if __name__ == "__main__":
    main()
