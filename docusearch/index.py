"""
Indexing system for document storage
"""

import math
from collections import defaultdict
from collections.abc import Mapping, MutableMapping
from collections.abc import Set as AbstractSet


class ForwardIndex:
    """Forward index mapping documents to word frequencies"""

    def __init__(self):
        self._doc_id_to_document: MutableMapping[str, MutableMapping[str, int]] = {}
        self._doc_id_to_doc_length: MutableMapping[str, int] = {}

    def add_document(self, doc_id: str, word_counts: MutableMapping[str, int]) -> None:
        """Add a document with its word frequencies"""
        self._doc_id_to_document[doc_id] = word_counts.copy()
        self._doc_id_to_doc_length[doc_id] = sum(word_counts.values())

    def get_word_count(self, doc_id: str, word: str) -> int:
        """Get the count of a word in a document"""
        return self._doc_id_to_document.get(doc_id, {}).get(word.lower(), 0)

    def get_document_words(self, doc_id: str) -> MutableMapping[str, int]:
        """Get all words and their counts for a document"""
        return self._doc_id_to_document.get(doc_id, {}).copy()

    def get_document_length(self, doc_id: str) -> int:
        """Get the total number of words in a document"""
        return self._doc_id_to_doc_length.get(doc_id, 0)

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index"""
        if doc_id in self._doc_id_to_document:
            del self._doc_id_to_document[doc_id]
            del self._doc_id_to_doc_length[doc_id]
            return True
        return False

    def get_all_document_ids(self) -> AbstractSet[str]:
        """Get all document IDs"""
        return set(self._doc_id_to_document.keys())

    def get_tf(self, doc_id: str, word: str) -> float:
        """Calculate Term Frequency for a word in a document"""
        word_count = self.get_word_count(doc_id, word)
        doc_length = self.get_document_length(doc_id)
        return word_count / doc_length if doc_length > 0 else 0


class ReverseIndex:
    """Reverse index mapping words to documents"""

    def __init__(self):
        self._word_to_doc_id_to_count: MutableMapping[str, MutableMapping[str, int]] = (
            defaultdict(dict)
        )
        self._word_to_freq: MutableMapping[str, int] = defaultdict(int)
        self._total_documents = 0

    def add_document(self, doc_id: str, word_counts: MutableMapping[str, int]) -> None:
        """Add a document's words to the reverse index"""
        for word, count in word_counts.items():
            word_lower = word.lower()
            is_new_word_in_doc = doc_id not in self._word_to_doc_id_to_count[word_lower]

            self._word_to_doc_id_to_count[word_lower][doc_id] = count

            if is_new_word_in_doc:
                self._word_to_freq[word_lower] += 1

        self._total_documents += 1

    def get_documents_for_word(self, word: str) -> Mapping[str, int]:
        """Get all documents containing a word and their counts"""
        return self._word_to_doc_id_to_count.get(word.lower(), {}).copy()

    def get_document_frequency(self, word: str) -> int:
        """Get the number of documents containing a word"""
        return self._word_to_freq.get(word.lower(), 0)

    def get_idf(self, word: str) -> float:
        """Calculate Inverse Document Frequency for a word"""
        doc_freq = self.get_document_frequency(word)
        if doc_freq == 0:
            return 0
        return math.log2((self._total_documents + 1) / (doc_freq + 1)) + 1

    def remove_document(
        self, doc_id: str, word_counts: MutableMapping[str, int]
    ) -> None:
        """Remove a document's words from the reverse index"""
        for word in word_counts:
            word_lower = word.lower()
            if doc_id in self._word_to_doc_id_to_count[word_lower]:
                del self._word_to_doc_id_to_count[word_lower][doc_id]

                if not self._word_to_doc_id_to_count[word_lower]:
                    del self._word_to_doc_id_to_count[word_lower]
                    del self._word_to_freq[word_lower]
                else:
                    self._word_to_freq[word_lower] -= 1

        self._total_documents = max(0, self._total_documents - 1)

    def get_all_words(self) -> AbstractSet[str]:
        """Get all words in the index"""
        return set(self._word_to_doc_id_to_count.keys())

    def get_tf_idf(self, doc_id: str, word: str, forward_index: ForwardIndex) -> float:
        """Calculate TF-IDF score for a word in a document"""
        tf = forward_index.get_tf(doc_id, word)
        idf = self.get_idf(word)
        return tf * idf
