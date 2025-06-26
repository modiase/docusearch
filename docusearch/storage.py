"""
Main document storage class with TF-IDF search
"""

import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .index import ForwardIndex
from .trie import Trie


class DocumentStorage:
    """In-memory document storage with TF-IDF search capabilities"""

    def __init__(self):
        self.trie = Trie()
        self.forward_index = ForwardIndex()
        self.documents: Dict[str, str] = {}  # doc_id -> content
        self.doc_counter = 0
        self.total_documents = 0

    def add_document_from_path(self, file_path: str) -> List[str]:
        """Add a document from a file path or all files in a directory

        Args:
            file_path: Path to a file or directory

        Returns:
            List of document IDs that were added
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {file_path}")

        if path.is_file():
            # Single file
            return [self._add_single_file(path)]
        elif path.is_dir():
            # Directory - add all files
            return self._add_directory(path)
        else:
            raise ValueError(f"Path is neither a file nor directory: {file_path}")

    def _add_single_file(self, file_path: Path) -> str:
        """Add a single file to the storage"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        return self.add_document(content, str(file_path))

    def _add_directory(self, dir_path: Path) -> List[str]:
        """Add all files in a directory to the storage"""
        added_docs = []

        # Common text file extensions
        text_extensions = {
            ".txt",
            ".md",
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".xml",
            ".csv",
            ".tsv",
            ".log",
            ".rst",
            ".tex",
            ".adoc",
            ".org",
        }

        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in text_extensions:
                try:
                    doc_id = self._add_single_file(file_path)
                    added_docs.append(doc_id)
                except Exception as e:
                    # Log error but continue with other files
                    print(f"Warning: Could not add {file_path}: {e}")

        return added_docs

    def add_document(self, content: str, doc_id: Optional[str] = None) -> str:
        """Add a document with given content"""
        if doc_id is None:
            self.doc_counter += 1
            doc_id = f"doc_{self.doc_counter}"

        # Tokenize and count words
        words = self._tokenize(content)
        word_counts = Counter(words)

        # Store document content
        self.documents[doc_id] = content

        # Update forward index
        self.forward_index.add_document(doc_id, word_counts)

        # Update trie with new words and document mappings
        for word, count in word_counts.items():
            # Insert word if not already present
            if not self.trie.search(word):
                self.trie.insert(word)
            # Add document to word's document set
            self.trie.add_document_to_word(word, doc_id, count)

        self.total_documents += 1
        return doc_id

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from storage"""
        if doc_id not in self.documents:
            return False

        # Get word counts before removal
        word_counts = self.forward_index.get_document_words(doc_id)

        # Remove from forward index
        self.forward_index.remove_document(doc_id)

        # Remove document from trie word mappings
        for word in word_counts:
            self.trie.remove_document_from_word(word, doc_id)

        # Remove from documents
        del self.documents[doc_id]

        # Clean up empty words from trie
        self.trie.cleanup_empty_words()

        self.total_documents = max(0, self.total_documents - 1)
        return True

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Search for documents using TF-IDF scoring

        Returns:
            List of tuples (doc_id, score, content_preview)
        """
        query_words = self._tokenize(query.lower())
        if not query_words:
            return []

        # Calculate TF-IDF scores for each document
        doc_scores: Dict[str, float] = {}

        for word in query_words:
            # Get documents containing this word
            docs_with_word = self.trie.get_documents_for_word(word)

            for doc_id, count in docs_with_word.items():
                # Calculate TF-IDF score for this word in this document
                tf_idf = self._calculate_tf_idf(doc_id, word)

                # Add to document's total score
                doc_scores[doc_id] = doc_scores.get(doc_id, 0) + tf_idf

        # Sort by score and return top-k results
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            content = self.documents.get(doc_id, "")
            preview = self._get_content_preview(content, query_words)
            results.append((doc_id, score, preview))

        return results

    def search_by_prefix(
        self, prefix: str, top_k: int = 5
    ) -> List[Tuple[str, float, str]]:
        """
        Search for documents using prefix matching on query terms

        Returns:
            List of tuples (doc_id, score, content_preview)
        """
        if not prefix.strip():
            return []

        # Get all documents containing words that start with the prefix
        docs_with_prefix = self.trie.get_documents_for_prefix(prefix.lower())

        if not docs_with_prefix:
            return []

        # Calculate scores based on word frequency (simplified scoring for prefix search)
        doc_scores: Dict[str, float] = {}

        for doc_id, total_count in docs_with_prefix.items():
            # Simple scoring: normalize by document length
            doc_length = self.forward_index.get_document_length(doc_id)
            if doc_length > 0:
                doc_scores[doc_id] = total_count / doc_length

        # Sort by score and return top-k results
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            content = self.documents.get(doc_id, "")
            preview = self._get_content_preview(content, [prefix])
            results.append((doc_id, score, preview))

        return results

    def prefix_search(self, prefix: str) -> List[str]:
        """Search for words that start with the given prefix"""
        return self.trie.starts_with(prefix)

    def get_document_info(self, doc_id: str) -> Optional[Dict]:
        """Get information about a specific document"""
        if doc_id not in self.documents:
            return None

        word_counts = self.forward_index.get_document_words(doc_id)
        doc_length = self.forward_index.get_document_length(doc_id)

        return {
            "doc_id": doc_id,
            "content": self.documents[doc_id],
            "word_counts": word_counts,
            "total_words": doc_length,
            "unique_words": len(word_counts),
        }

    def get_stats(self) -> Dict:
        """Get statistics about the document storage"""
        return {
            "total_documents": len(self.documents),
            "total_words": len(self.trie.get_all_words()),
            "total_documents_in_index": self.total_documents,
        }

    def _calculate_tf_idf(self, doc_id: str, word: str) -> float:
        """Calculate TF-IDF score for a word in a document"""
        # Calculate TF
        tf = self.forward_index.get_tf(doc_id, word)

        # Calculate IDF
        doc_freq = self.trie.get_document_frequency(word)
        if doc_freq == 0:
            return 0
        # Use log2((N+1)/(df+1)) + 1 to ensure non-zero scores
        idf = math.log2((self.total_documents + 1) / (doc_freq + 1)) + 1

        return tf * idf

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove punctuation and split into words
        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        # Filter out very short words (likely noise)
        words = [word for word in words if len(word) > 1]
        return words

    def _get_content_preview(
        self, content: str, query_words: List[str], max_length: int = 200
    ) -> str:
        """Generate a preview of the content highlighting query words"""
        if len(content) <= max_length:
            return content

        # Find the first occurrence of any query word
        content_lower = content.lower()
        first_pos = len(content)

        for word in query_words:
            pos = content_lower.find(word)
            if pos != -1 and pos < first_pos:
                first_pos = pos

        # Extract preview around the first query word
        start = max(0, first_pos - 50)
        end = min(len(content), start + max_length)

        preview = content[start:end]

        # Add ellipsis if we're not at the beginning/end
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."

        return preview

    def smart_search(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        r"""
        Smart search that automatically chooses between exact and prefix search

        Rules:
        - If query ends with *, use prefix search (removing the *)
        - Otherwise use exact word matching
        - Interpret \* as literal * (escape the wildcard)

        Returns:
            List of tuples (doc_id, score, content_preview)
        """
        if not query.strip():
            return []

        # Handle escaped asterisks
        query = query.replace("\\*", "___ESCAPED_ASTERISK___")

        # Check if query ends with * (prefix search)
        if query.endswith("*"):
            prefix = query[:-1].strip()  # Remove the *
            if prefix:  # Only search if there's a prefix
                return self.search_by_prefix(prefix, top_k)
            return []

        # Restore escaped asterisks
        query = query.replace("___ESCAPED_ASTERISK___", "*")

        # Use exact search
        return self.search(query, top_k)
