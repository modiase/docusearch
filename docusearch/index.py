"""
Indexing system for document storage
"""

import math
from collections import defaultdict
from typing import Dict, Set


class ForwardIndex:
    """Forward index mapping documents to word frequencies"""

    def __init__(self):
        # doc_id -> {word -> count}
        self.documents: Dict[str, Dict[str, int]] = {}
        # doc_id -> total_words
        self.doc_lengths: Dict[str, int] = {}

    def add_document(self, doc_id: str, word_counts: Dict[str, int]) -> None:
        """Add a document with its word frequencies"""
        self.documents[doc_id] = word_counts.copy()
        self.doc_lengths[doc_id] = sum(word_counts.values())

    def get_word_count(self, doc_id: str, word: str) -> int:
        """Get the count of a word in a document"""
        return self.documents.get(doc_id, {}).get(word.lower(), 0)

    def get_document_words(self, doc_id: str) -> Dict[str, int]:
        """Get all words and their counts for a document"""
        return self.documents.get(doc_id, {}).copy()

    def get_document_length(self, doc_id: str) -> int:
        """Get the total number of words in a document"""
        return self.doc_lengths.get(doc_id, 0)

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.doc_lengths[doc_id]
            return True
        return False

    def get_all_documents(self) -> Set[str]:
        """Get all document IDs"""
        return set(self.documents.keys())

    def get_tf(self, doc_id: str, word: str) -> float:
        """Calculate Term Frequency for a word in a document"""
        word_count = self.get_word_count(doc_id, word)
        doc_length = self.get_document_length(doc_id)
        return word_count / doc_length if doc_length > 0 else 0


class ReverseIndex:
    """Reverse index mapping words to documents"""

    def __init__(self):
        # word -> {doc_id -> count}
        self.word_to_docs: Dict[str, Dict[str, int]] = defaultdict(dict)
        # word -> document frequency (number of docs containing the word)
        self.word_doc_freq: Dict[str, int] = defaultdict(int)
        # Total number of documents
        self.total_documents = 0

    def add_document(self, doc_id: str, word_counts: Dict[str, int]) -> None:
        """Add a document's words to the reverse index"""
        for word, count in word_counts.items():
            word_lower = word.lower()
            # Check if this is the first time this word appears in this document
            is_new_word_in_doc = doc_id not in self.word_to_docs[word_lower]

            self.word_to_docs[word_lower][doc_id] = count

            # Update document frequency if this is the first occurrence of this word in this document
            if is_new_word_in_doc:
                self.word_doc_freq[word_lower] += 1

        self.total_documents += 1

    def get_documents_for_word(self, word: str) -> Dict[str, int]:
        """Get all documents containing a word and their counts"""
        return self.word_to_docs.get(word.lower(), {}).copy()

    def get_document_frequency(self, word: str) -> int:
        """Get the number of documents containing a word"""
        return self.word_doc_freq.get(word.lower(), 0)

    def get_idf(self, word: str) -> float:
        """Calculate Inverse Document Frequency for a word"""
        doc_freq = self.get_document_frequency(word)
        if doc_freq == 0:
            return 0
        # Use log2((N+1)/(df+1)) + 1 to ensure non-zero scores
        return math.log2((self.total_documents + 1) / (doc_freq + 1)) + 1

    def remove_document(self, doc_id: str, word_counts: Dict[str, int]) -> None:
        """Remove a document's words from the reverse index"""
        for word in word_counts:
            word_lower = word.lower()
            if doc_id in self.word_to_docs[word_lower]:
                del self.word_to_docs[word_lower][doc_id]

                # If no documents contain this word anymore, remove it
                if not self.word_to_docs[word_lower]:
                    del self.word_to_docs[word_lower]
                    del self.word_doc_freq[word_lower]
                else:
                    # Decrease document frequency
                    self.word_doc_freq[word_lower] -= 1

        self.total_documents = max(0, self.total_documents - 1)

    def get_all_words(self) -> Set[str]:
        """Get all words in the index"""
        return set(self.word_to_docs.keys())

    def get_tf_idf(self, doc_id: str, word: str, forward_index: ForwardIndex) -> float:
        """Calculate TF-IDF score for a word in a document"""
        tf = forward_index.get_tf(doc_id, word)
        idf = self.get_idf(word)
        return tf * idf
