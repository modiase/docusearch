"""
Trie data structure for efficient prefix searching
"""

from collections.abc import MutableMapping
from typing import Dict, List, Optional, Set


class TrieNode:
    """A node in the trie data structure"""

    def __init__(self):
        self._children: MutableMapping[str, TrieNode] = {}
        self._is_end_of_word: bool = False
        self._word: Optional[str] = None
        self._containing_documents: Set[str] = set()
        self._doc_to_word_count: MutableMapping[str, int] = {}


class Trie:
    """Trie data structure for efficient prefix searching with document mappings"""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Insert a word into the trie"""
        node = self.root
        for char in word.lower():
            if char not in node._children:
                node._children[char] = TrieNode()
            node = node._children[char]
        node._is_end_of_word = True
        node._word = word.lower()

    def add_document_to_word(self, word: str, doc_id: str, count: int = 1) -> None:
        """Add a document to a word's document set"""
        node = self._find_node(word.lower())
        if node and node._is_end_of_word:
            node._containing_documents.add(doc_id)
            node._doc_to_word_count[doc_id] = count

    def remove_document_from_word(self, word: str, doc_id: str) -> bool:
        """Remove a document from a word's document set"""
        node = self._find_node(word.lower())
        if node and node._is_end_of_word:
            if doc_id in node._containing_documents:
                node._containing_documents.remove(doc_id)
                if doc_id in node._doc_to_word_count:
                    del node._doc_to_word_count[doc_id]
                return True
        return False

    def get_documents_for_word(self, word: str) -> Dict[str, int]:
        """Get all documents containing a word and their counts"""
        node = self._find_node(word.lower())
        if node and node._is_end_of_word:
            return node._doc_to_word_count.copy()
        return {}

    def get_document_frequency(self, word: str) -> int:
        """Get the number of documents containing a word"""
        node = self._find_node(word.lower())
        if node and node._is_end_of_word:
            return len(node._containing_documents)
        return 0

    def search(self, word: str) -> bool:
        """Search for an exact word in the trie"""
        node = self._find_node(word.lower())
        return node is not None and node._is_end_of_word

    def starts_with(self, prefix: str) -> List[str]:
        """Find all words that start with the given prefix"""
        node = self._find_node(prefix.lower())
        if node is None:
            return []

        words = []
        self._collect_words(node, words)
        return words

    def get_documents_for_prefix(self, prefix: str) -> Dict[str, int]:
        """Get all documents containing words that start with the given prefix"""
        node = self._find_node(prefix.lower())
        if node is None:
            return {}

        doc_counts: MutableMapping[str, int] = {}
        self._collect_documents_from_node(node, doc_counts)
        return doc_counts

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """Find the node corresponding to the given prefix"""
        node = self.root
        for char in prefix:
            if char not in node._children:
                return None
            node = node._children[char]
        return node

    def _collect_words(self, node: TrieNode, words: List[str]) -> None:
        """Collect all words from the given node and its descendants"""
        if node._is_end_of_word and node._word:
            words.append(node._word)

        for child in node._children.values():
            self._collect_words(child, words)

    def _collect_documents_from_node(
        self, node: TrieNode, doc_counts: Dict[str, int]
    ) -> None:
        """Collect all documents from the given node and its descendants"""
        if node._is_end_of_word:
            for doc_id, count in node._doc_to_word_count.items():
                doc_counts[doc_id] = doc_counts.get(doc_id, 0) + count

        for child in node._children.values():
            self._collect_documents_from_node(child, doc_counts)

    def remove(self, word: str) -> bool:
        """Remove a word from the trie (only if no documents contain it)"""
        node = self._find_node(word.lower())
        if node and node._is_end_of_word and len(node._containing_documents) == 0:
            return self._remove_helper(self.root, word.lower(), 0)
        return False

    def _remove_helper(self, node: TrieNode, word: str, index: int) -> bool:
        """Helper method to remove a word from the trie"""
        if index == len(word):
            if not node._is_end_of_word:
                return False
            node._is_end_of_word = False
            node._word = None
            return len(node._children) == 0

        char = word[index]
        if char not in node._children:
            return False

        should_delete_child = self._remove_helper(node._children[char], word, index + 1)

        if should_delete_child:
            del node._children[char]
            return len(node._children) == 0 and not node._is_end_of_word

        return False

    def get_all_words(self) -> List[str]:
        """Get all words stored in the trie"""
        words = []
        self._collect_words(self.root, words)
        return words

    def cleanup_empty_words(self) -> None:
        """Remove words that have no documents"""
        words_to_remove = []
        for word in self.get_all_words():
            node = self._find_node(word)
            if node and len(node._containing_documents) == 0:
                words_to_remove.append(word)

        for word in words_to_remove:
            self.remove(word)
