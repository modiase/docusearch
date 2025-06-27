"""
Main document storage class.
"""

from __future__ import annotations


import json
import math
import re
import uuid
from collections import Counter
from pathlib import Path
from collections.abc import MutableMapping, Optional, Sequence, Tuple

from .index import ForwardIndex
from .trie import Trie


def generate_doc_id() -> str:
    """Generate a unique document ID"""
    return f"doc_{uuid.uuid4()}"


class DocumentStorage:
    """Searchable document storage"""

    def __init__(self):
        self.trie = Trie()
        self._forward_index = ForwardIndex()
        self._doc_id_to_document: MutableMapping[str, str] = {}
        self._total_documents = 0

    def add_document_from_path(self, file_path: str) -> Sequence[str]:
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
            return [self._add_single_file(path)]
        elif path.is_dir():
            return self._add_directory(path)
        else:
            raise ValueError(f"Path is neither a file nor directory: {file_path}")

    def _add_single_file(self, file_path: Path) -> str:
        """Add a single file to the storage"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        return self.add_document(content, str(file_path))

    def _add_directory(self, dir_path: Path) -> Sequence[str]:
        """Add all files in a directory to the storage"""
        added_docs = []

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
                    print(f"Warning: Could not add {file_path}: {e}")

        return added_docs

    def add_document(self, content: str, doc_id: Optional[str] = None) -> str:
        """Add a document with given content"""
        if doc_id is not None and doc_id in self._doc_id_to_document:
            raise ValueError(f"Document with ID {doc_id} already exists")

        doc_id = generate_doc_id() if doc_id is None else doc_id

        word_counts = Counter(self._tokenize(content))

        self._doc_id_to_document[doc_id] = content

        self._forward_index.add_document(doc_id, word_counts)

        for word, count in word_counts.items():
            if not self.trie.search(word):
                self.trie.insert(word)
            self.trie.add_document_to_word(word, doc_id, count)

        self._total_documents += 1
        return doc_id

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from storage"""
        if doc_id not in self._doc_id_to_document:
            return False

        word_counts = self._forward_index.get_document_words(doc_id)

        self._forward_index.remove_document(doc_id)

        for word in word_counts:
            self.trie.remove_document_from_word(word, doc_id)

        del self._doc_id_to_document[doc_id]

        self.trie.cleanup_empty_words()

        self._total_documents = max(0, self._total_documents - 1)
        return True

    def search(self, query: str, top_k: int = 5) -> Sequence[Tuple[str, float, str]]:
        """
        Search for documents using TF-IDF scoring

        Returns:
            List of tuples (doc_id, score, content_preview)
        """
        query_words = self._tokenize(query.lower())
        if not query_words:
            return []

        doc_scores: MutableMapping[str, float] = {}

        for word in query_words:
            # Get documents containing this word
            docs_with_word = self.trie.get_documents_for_word(word)

            for doc_id in docs_with_word:
                tf_idf = self._calculate_tf_idf(doc_id, word)

                doc_scores[doc_id] = doc_scores.get(doc_id, 0) + tf_idf

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            content = self._doc_id_to_document.get(doc_id, "")
            preview = self._get_content_preview(content, query_words)
            results.append((doc_id, score, preview))

        return results

    def search_by_prefix(
        self, prefix: str, top_k: int = 5
    ) -> Sequence[Tuple[str, float, str]]:
        """
        Search for documents using prefix matching on query terms

        Returns:
            List of tuples (doc_id, score, content_preview)
        """
        if not prefix.strip():
            return []

        docs_with_prefix = self.trie.get_documents_for_prefix(prefix.lower())

        if not docs_with_prefix:
            return []

        doc_scores: MutableMapping[str, float] = {}

        for doc_id, total_count in docs_with_prefix.items():
            doc_length = self._forward_index.get_document_length(doc_id)
            if doc_length > 0:
                doc_scores[doc_id] = total_count / doc_length

        # Sort by score and return top-k results
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            content = self._doc_id_to_document.get(doc_id, "")
            preview = self._get_content_preview(content, [prefix])
            results.append((doc_id, score, preview))

        return results

    def prefix_search(self, prefix: str) -> List[str]:
        """Search for words that start with the given prefix"""
        return self.trie.starts_with(prefix)

    def get_document_info(self, doc_id: str) -> Optional[MutableMapping]:
        """Get information about a specific document"""
        if doc_id not in self._doc_id_to_document:
            return None

        word_counts = self._forward_index.get_document_words(doc_id)
        doc_length = self._forward_index.get_document_length(doc_id)

        return {
            "doc_id": doc_id,
            "content": self._doc_id_to_document[doc_id],
            "word_counts": word_counts,
            "total_words": doc_length,
            "unique_words": len(word_counts),
        }

    def get_stats(self) -> MutableMapping:
        """Get statistics about the document storage"""
        return {
            "total_documents": len(self._doc_id_to_document),
            "total_words": len(self.trie.get_all_words()),
            "total_documents_in_index": self._total_documents,
        }

    def _calculate_tf_idf(self, doc_id: str, word: str) -> float:
        """Calculate TF-IDF score for a word in a document"""
        tf = self._forward_index.get_tf(doc_id, word)
        doc_freq = self.trie.get_document_frequency(word)
        if doc_freq == 0:
            return 0
        idf = math.log2((self._total_documents + 1) / (doc_freq + 1)) + 1

        return tf * idf

    def _tokenize(self, text: str) -> Iterable[str]:
        """Tokenize text into words"""
        return (
            word for word in re.findall(r"\b[a-zA-Z]+\b", text.lower()) if len(word) > 1
        )

    def _get_content_preview(
        self, content: str, query_words: List[str], max_length: int = 200
    ) -> str:
        """Generate a preview of the content highlighting query words"""
        if len(content) <= max_length:
            return content

        content_lower = content.lower()
        first_pos = len(content)

        for word in query_words:
            pos = content_lower.find(word)
            if pos != -1 and pos < first_pos:
                first_pos = pos

        start = max(0, first_pos - 50)
        end = min(len(content), start + max_length)

        preview = content[start:end]

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

        query = query.replace("\\*", "___ESCAPED_ASTERISK___")

        if query.endswith("*"):
            prefix = query[:-1].strip()  # Remove the *
            if prefix:  # Only search if there's a prefix
                return self.search_by_prefix(prefix, top_k)
            return []

        query = query.replace("___ESCAPED_ASTERISK___", "*")

        return self.search(query, top_k)

    def save(self, file_path: Path) -> None:
        with open(file_path, "w") as f:
            json.dump(
                {
                    "documents": self._doc_id_to_document,
                    "doc_counter": self._doc_counter,
                    "total_documents": self._total_documents,
                    "forward_index": {
                        "documents": self._forward_index._doc_id_to_document,
                        "doc_lengths": self._forward_index._doc_id_to_doc_length,
                    },
                },
                f,
                indent=2,
            )

    @classmethod
    def load(cls, file_path: Path) -> "DocumentStorage":
        with open(file_path, "r") as f:
            data = json.load(f)

        storage = cls(
            documents=data["documents"],
            doc_counter=data["doc_counter"],
            total_documents=data["total_documents"],
            forward_index=ForwardIndex(
                documents=data["forward_index"]["documents"],
                doc_lengths=data["forward_index"]["doc_lengths"],
            ),
        )

        for doc_id, word_counts in storage._forward_index._doc_id_to_document.items():
            for word, count in word_counts.items():
                if not storage.trie.search(word):
                    # TODO: Use a bloom filter?
                    storage.trie.insert(word)
                storage.trie.add_document_to_word(word, doc_id, count)

        return storage
