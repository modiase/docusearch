package index

import "strings"

// ForwardIndex maps documents to word frequencies
type ForwardIndex struct {
	docIDToDocument map[string]map[string]int
	docIDToDocLength map[string]int
}

// NewForwardIndex creates a new forward index instance
func NewForwardIndex() *ForwardIndex {
	return &ForwardIndex{
		docIDToDocument:  make(map[string]map[string]int),
		docIDToDocLength: make(map[string]int),
	}
}

// NewForwardIndexWithData creates a forward index with existing data
func NewForwardIndexWithData(documents map[string]map[string]int, docLengths map[string]int) *ForwardIndex {
	return &ForwardIndex{
		docIDToDocument:  documents,
		docIDToDocLength: docLengths,
	}
}

// AddDocument adds a document with its word frequencies
func (fi *ForwardIndex) AddDocument(docID string, wordCounts map[string]int) {
	// Copy the word counts map
	docWordCounts := make(map[string]int)
	totalWords := 0
	
	for word, count := range wordCounts {
		docWordCounts[word] = count
		totalWords += count
	}
	
	fi.docIDToDocument[docID] = docWordCounts
	fi.docIDToDocLength[docID] = totalWords
}

// GetWordCount returns the count of a word in a document
func (fi *ForwardIndex) GetWordCount(docID, word string) int {
	if doc, exists := fi.docIDToDocument[docID]; exists {
		return doc[strings.ToLower(word)]
	}
	return 0
}

// GetDocumentWords returns all words and their counts for a document
func (fi *ForwardIndex) GetDocumentWords(docID string) map[string]int {
	if doc, exists := fi.docIDToDocument[docID]; exists {
		// Return a copy to prevent external modification
		result := make(map[string]int)
		for word, count := range doc {
			result[word] = count
		}
		return result
	}
	return make(map[string]int)
}

// GetDocumentLength returns the total number of words in a document
func (fi *ForwardIndex) GetDocumentLength(docID string) int {
	if length, exists := fi.docIDToDocLength[docID]; exists {
		return length
	}
	return 0
}

// RemoveDocument removes a document from the index
func (fi *ForwardIndex) RemoveDocument(docID string) bool {
	if _, exists := fi.docIDToDocument[docID]; exists {
		delete(fi.docIDToDocument, docID)
		delete(fi.docIDToDocLength, docID)
		return true
	}
	return false
}

// GetAllDocumentIDs returns all document IDs
func (fi *ForwardIndex) GetAllDocumentIDs() []string {
	var docIDs []string
	for docID := range fi.docIDToDocument {
		docIDs = append(docIDs, docID)
	}
	return docIDs
}

// GetTF calculates Term Frequency for a word in a document
func (fi *ForwardIndex) GetTF(docID, word string) float64 {
	wordCount := fi.GetWordCount(docID, word)
	docLength := fi.GetDocumentLength(docID)
	
	if docLength > 0 {
		return float64(wordCount) / float64(docLength)
	}
	return 0.0
}

// GetDocuments returns the internal document map (for serialization)
func (fi *ForwardIndex) GetDocuments() map[string]map[string]int {
	return fi.docIDToDocument
}

// GetDocLengths returns the internal doc lengths map (for serialization)
func (fi *ForwardIndex) GetDocLengths() map[string]int {
	return fi.docIDToDocLength
} 