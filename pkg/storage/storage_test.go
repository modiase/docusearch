package storage

import (
	"os"
	"path/filepath"
	"testing"
)

func TestAddDocument(t *testing.T) {
	store := New()
	
	docID := store.AddDocument("This is a test document.", "test_doc")
	
	if docID != "test_doc" {
		t.Errorf("Expected docID to be 'test_doc', got %s", docID)
	}
	
	docInfo := store.GetDocumentInfo(docID)
	if docInfo == nil {
		t.Error("Expected document info to exist")
		return
	}
	
	if docInfo.Content != "This is a test document." {
		t.Errorf("Expected content to match, got %s", docInfo.Content)
	}
}

func TestAddDocumentAutoID(t *testing.T) {
	store := New()
	
	docID := store.AddDocument("Another test document.", "")
	
	if docID == "" {
		t.Error("Expected auto-generated docID to be non-empty")
	}
	
	docInfo := store.GetDocumentInfo(docID)
	if docInfo == nil {
		t.Error("Expected document info to exist")
		return
	}
	
	if docInfo.Content != "Another test document." {
		t.Errorf("Expected content to match, got %s", docInfo.Content)
	}
}

func TestDeleteDocument(t *testing.T) {
	store := New()
	
	docID := store.AddDocument("Test document to delete.", "delete_test")
	
	// Verify document exists
	docInfo := store.GetDocumentInfo(docID)
	if docInfo == nil {
		t.Error("Expected document to exist before deletion")
		return
	}
	
	// Delete document
	result := store.RemoveDocument(docID)
	if !result {
		t.Error("Expected removal to return true")
	}
	
	// Verify document is removed
	docInfoAfter := store.GetDocumentInfo(docID)
	if docInfoAfter != nil {
		t.Error("Expected document to be removed")
	}
	
	stats := store.GetStats()
	if stats.TotalDocuments != 0 {
		t.Errorf("Expected 0 documents, got %d", stats.TotalDocuments)
	}
}

func TestDeleteNonexistentDocument(t *testing.T) {
	store := New()
	
	result := store.RemoveDocument("nonexistent")
	if result {
		t.Error("Expected removal of nonexistent document to return false")
	}
	
	stats := store.GetStats()
	if stats.TotalDocuments != 0 {
		t.Errorf("Expected 0 documents, got %d", stats.TotalDocuments)
	}
}

func TestGetDocumentInfo(t *testing.T) {
	store := New()
	
	store.AddDocument("This is a test document with multiple words.", "info_test")
	
	info := store.GetDocumentInfo("info_test")
	if info == nil {
		t.Error("Expected document info to exist")
		return
	}
	
	if info.TotalWords != 8 { // "this", "is", "test", "document", "with", "multiple", "words"
		t.Errorf("Expected 8 words, got %d", info.TotalWords)
	}
	
	if info.UniqueWords != 8 {
		t.Errorf("Expected 8 unique words, got %d", info.UniqueWords)
	}
	
	if info.Content == "" {
		t.Error("Expected content to be present")
	}
}

func TestGetNonexistentDocumentInfo(t *testing.T) {
	store := New()
	
	info := store.GetDocumentInfo("nonexistent")
	if info != nil {
		t.Error("Expected nil for nonexistent document")
	}
}

func TestGetStatsEmpty(t *testing.T) {
	store := New()
	
	stats := store.GetStats()
	if stats.TotalDocuments != 0 {
		t.Errorf("Expected 0 documents, got %d", stats.TotalDocuments)
	}
	if stats.TotalWords != 0 {
		t.Errorf("Expected 0 words, got %d", stats.TotalWords)
	}
}

func TestGetStatsWithDocuments(t *testing.T) {
	store := New()
	
	store.AddDocument("First document.", "doc1")
	store.AddDocument("Second document with more words.", "doc2")
	
	stats := store.GetStats()
	if stats.TotalDocuments != 2 {
		t.Errorf("Expected 2 documents, got %d", stats.TotalDocuments)
	}
	if stats.TotalWords == 0 {
		t.Error("Expected non-zero word count")
	}
}

func TestSearchEmptyStorage(t *testing.T) {
	store := New()
	
	results := store.Search("test", 5)
	if len(results) != 0 {
		t.Errorf("Expected no results, got %d", len(results))
	}
}

func TestSearchSingleDocument(t *testing.T) {
	store := New()
	
	store.AddDocument("This document contains python programming.", "python_doc")
	
	results := store.Search("python", 5)
	if len(results) != 1 {
		t.Errorf("Expected 1 result, got %d", len(results))
		return
	}
	
	if results[0].DocID != "python_doc" {
		t.Errorf("Expected docID 'python_doc', got %s", results[0].DocID)
	}
	
	if results[0].Score <= 0 {
		t.Error("Expected positive score")
	}
}

func TestSearchMultipleDocuments(t *testing.T) {
	store := New()
	
	store.AddDocument("Python programming language.", "doc1")
	store.AddDocument("Java programming language.", "doc2")
	store.AddDocument("Web development with HTML.", "doc3")
	
	results := store.Search("programming", 5)
	if len(results) != 2 {
		t.Errorf("Expected 2 results, got %d", len(results))
		return
	}
	
	docIDs := make(map[string]bool)
	for _, result := range results {
		docIDs[result.DocID] = true
	}
	
	if !docIDs["doc1"] || !docIDs["doc2"] {
		t.Error("Expected doc1 and doc2 in results")
	}
}

func TestPrefixSearchEmpty(t *testing.T) {
	store := New()
	
	words := store.PrefixSearch("test")
	if len(words) != 0 {
		t.Errorf("Expected no words, got %d", len(words))
	}
}

func TestPrefixSearchWithDocuments(t *testing.T) {
	store := New()
	
	store.AddDocument("Python programming.", "doc1")
	store.AddDocument("Java programming.", "doc2")
	store.AddDocument("JavaScript programming.", "doc3")
	
	words := store.PrefixSearch("prog")
	found := false
	for _, word := range words {
		if word == "programming" {
			found = true
			break
		}
	}
	if !found {
		t.Error("Expected to find 'programming' with prefix 'prog'")
	}
}

func TestTFIDFScoring(t *testing.T) {
	store := New()
	
	// Add documents with known word frequencies
	store.AddDocument("python python python", "doc1") // 3 occurrences
	store.AddDocument("python java", "doc2")          // 1 occurrence
	store.AddDocument("java java", "doc3")            // 0 occurrences of python
	
	results := store.Search("python", 5)
	if len(results) != 2 {
		t.Errorf("Expected 2 results, got %d", len(results))
		return
	}
	
	// Find scores for doc1 and doc2
	var doc1Score, doc2Score float64
	for _, result := range results {
		if result.DocID == "doc1" {
			doc1Score = result.Score
		} else if result.DocID == "doc2" {
			doc2Score = result.Score
		}
	}
	
	// doc1 should have higher score than doc2 due to higher TF
	if doc1Score <= doc2Score {
		t.Errorf("Expected doc1 score (%.4f) > doc2 score (%.4f)", doc1Score, doc2Score)
	}
}

func TestSearchTopKLimit(t *testing.T) {
	store := New()
	
	store.AddDocument("python programming", "doc1")
	store.AddDocument("python development", "doc2")
	store.AddDocument("python scripting", "doc3")
	
	results := store.Search("python", 2)
	if len(results) != 2 {
		t.Errorf("Expected 2 results, got %d", len(results))
	}
}

func TestSearchCaseInsensitive(t *testing.T) {
	store := New()
	
	store.AddDocument("Python Programming", "doc1")
	
	resultsLower := store.Search("python", 5)
	resultsUpper := store.Search("PYTHON", 5)
	resultsMixed := store.Search("Python", 5)
	
	if len(resultsLower) != 1 || len(resultsUpper) != 1 || len(resultsMixed) != 1 {
		t.Error("Expected case insensitive search to work")
	}
	
	if resultsLower[0].DocID != resultsUpper[0].DocID || 
	   resultsLower[0].DocID != resultsMixed[0].DocID {
		t.Error("Expected same results regardless of case")
	}
}

func TestSmartSearch(t *testing.T) {
	store := New()
	
	store.AddDocument("Python programming language", "doc1")
	store.AddDocument("Progressive web apps", "doc2")
	
	// Test exact search
	results := store.SmartSearch("python", 5)
	if len(results) != 1 || results[0].DocID != "doc1" {
		t.Error("Expected exact search to find doc1")
	}
	
	// Test prefix search with wildcard
	results = store.SmartSearch("prog*", 5)
	if len(results) == 0 {
		t.Error("Expected prefix search to find documents")
	}
}

func TestSaveAndLoad(t *testing.T) {
	store := New()
	
	store.AddDocument("Test document for persistence", "test_doc")
	
	// Create temp file
	tmpFile := filepath.Join(os.TempDir(), "test_storage.json")
	defer os.Remove(tmpFile)
	
	// Save
	err := store.Save(tmpFile)
	if err != nil {
		t.Fatalf("Error saving: %v", err)
	}
	
	// Load
	loadedStore, err := Load(tmpFile)
	if err != nil {
		t.Fatalf("Error loading: %v", err)
	}
	
	// Verify loaded data
	docInfo := loadedStore.GetDocumentInfo("test_doc")
	if docInfo == nil {
		t.Error("Expected loaded document to exist")
		return
	}
	
	if docInfo.Content != "Test document for persistence" {
		t.Errorf("Expected content to match, got %s", docInfo.Content)
	}
	
	stats := loadedStore.GetStats()
	if stats.TotalDocuments != 1 {
		t.Errorf("Expected 1 document, got %d", stats.TotalDocuments)
	}
} 