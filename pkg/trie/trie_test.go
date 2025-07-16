package trie

import (
	"testing"
)

func TestTrieInsertAndSearch(t *testing.T) {
	tr := New()

	// Insert words
	tr.Insert("python")
	tr.Insert("programming")

	// Test exact search
	if !tr.Search("python") {
		t.Error("Expected to find 'python'")
	}
	if !tr.Search("programming") {
		t.Error("Expected to find 'programming'")
	}
	if tr.Search("nonexistent") {
		t.Error("Expected not to find 'nonexistent'")
	}

	// Test prefix search
	words := tr.StartsWith("py")
	found := false
	for _, word := range words {
		if word == "python" {
			found = true
			break
		}
	}
	if !found {
		t.Error("Expected to find 'python' with prefix 'py'")
	}

	words = tr.StartsWith("prog")
	found = false
	for _, word := range words {
		if word == "programming" {
			found = true
			break
		}
	}
	if !found {
		t.Error("Expected to find 'programming' with prefix 'prog'")
	}

	words = tr.StartsWith("xyz")
	if len(words) != 0 {
		t.Error("Expected no words with prefix 'xyz'")
	}
}

func TestTrieWordCounts(t *testing.T) {
	tr := New()

	tr.Insert("python")
	tr.AddDocumentToWord("python", "doc1", 2)
	tr.AddDocumentToWord("python", "doc2", 1)

	// Get word info
	docs := tr.GetDocumentsForWord("python")
	if docs["doc1"] != 2 {
		t.Errorf("Expected doc1 count to be 2, got %d", docs["doc1"])
	}
	if docs["doc2"] != 1 {
		t.Errorf("Expected doc2 count to be 1, got %d", docs["doc2"])
	}
}

func TestTrieDeleteWord(t *testing.T) {
	tr := New()

	tr.Insert("python")
	tr.AddDocumentToWord("python", "doc1", 1)
	tr.AddDocumentToWord("python", "doc2", 1)
	tr.Insert("programming")
	tr.AddDocumentToWord("programming", "doc1", 1)

	// Delete word from specific document
	tr.RemoveDocumentFromWord("python", "doc1")
	docs := tr.GetDocumentsForWord("python")
	if _, exists := docs["doc1"]; exists {
		t.Error("Expected doc1 to be removed from python")
	}
	if _, exists := docs["doc2"]; !exists {
		t.Error("Expected doc2 to still exist for python")
	}

	// Delete word completely
	tr.RemoveDocumentFromWord("python", "doc2")
	docs = tr.GetDocumentsForWord("python")
	if len(docs) != 0 {
		t.Error("Expected no documents for python after removal")
	}
}

func TestTrieEmptyOperations(t *testing.T) {
	tr := New()

	if tr.Search("any") {
		t.Error("Expected not to find 'any' in empty trie")
	}
	
	words := tr.StartsWith("any")
	if len(words) != 0 {
		t.Error("Expected no words with prefix 'any' in empty trie")
	}
	
	docs := tr.GetDocumentsForWord("any")
	if len(docs) != 0 {
		t.Error("Expected no documents for 'any' in empty trie")
	}
} 