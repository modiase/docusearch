package index

import (
	"math"
	"strings"
)

// ReverseIndex maps words to documents
type ReverseIndex struct {
	wordToDocIDToCount map[string]map[string]int
	wordToFreq         map[string]int
	totalDocuments     int
}

// NewReverseIndex creates a new reverse index instance
func NewReverseIndex() *ReverseIndex {
	return &ReverseIndex{
		wordToDocIDToCount: make(map[string]map[string]int),
		wordToFreq:         make(map[string]int),
		totalDocuments:     0,
	}
}

// AddDocument adds a document's words to the reverse index
func (ri *ReverseIndex) AddDocument(docID string, wordCounts map[string]int) {
	for word, count := range wordCounts {
		wordLower := strings.ToLower(word)
		
		// Initialize word entry if it doesn't exist
		if ri.wordToDocIDToCount[wordLower] == nil {
			ri.wordToDocIDToCount[wordLower] = make(map[string]int)
		}
		
		isNewWordInDoc := ri.wordToDocIDToCount[wordLower][docID] == 0
		
		ri.wordToDocIDToCount[wordLower][docID] = count
		
		if isNewWordInDoc {
			ri.wordToFreq[wordLower]++
		}
	}
	
	ri.totalDocuments++
}

// GetDocumentsForWord returns all documents containing a word and their counts
func (ri *ReverseIndex) GetDocumentsForWord(word string) map[string]int {
	wordLower := strings.ToLower(word)
	if docs, exists := ri.wordToDocIDToCount[wordLower]; exists {
		// Return a copy to prevent external modification
		result := make(map[string]int)
		for docID, count := range docs {
			result[docID] = count
		}
		return result
	}
	return make(map[string]int)
}

// GetDocumentFrequency returns the number of documents containing a word
func (ri *ReverseIndex) GetDocumentFrequency(word string) int {
	wordLower := strings.ToLower(word)
	if freq, exists := ri.wordToFreq[wordLower]; exists {
		return freq
	}
	return 0
}

// GetIDF calculates Inverse Document Frequency for a word
func (ri *ReverseIndex) GetIDF(word string) float64 {
	docFreq := ri.GetDocumentFrequency(word)
	if docFreq == 0 {
		return 0
	}
	return math.Log2(float64(ri.totalDocuments+1)/float64(docFreq+1)) + 1
}

// RemoveDocument removes a document's words from the reverse index
func (ri *ReverseIndex) RemoveDocument(docID string, wordCounts map[string]int) {
	for word := range wordCounts {
		wordLower := strings.ToLower(word)
		
		if docs, exists := ri.wordToDocIDToCount[wordLower]; exists {
			if _, docExists := docs[docID]; docExists {
				delete(docs, docID)
				
				if len(docs) == 0 {
					delete(ri.wordToDocIDToCount, wordLower)
					delete(ri.wordToFreq, wordLower)
				} else {
					ri.wordToFreq[wordLower]--
				}
			}
		}
	}
	
	if ri.totalDocuments > 0 {
		ri.totalDocuments--
	}
}

// GetAllWords returns all words in the index
func (ri *ReverseIndex) GetAllWords() []string {
	var words []string
	for word := range ri.wordToDocIDToCount {
		words = append(words, word)
	}
	return words
}

// GetTFIDF calculates TF-IDF score for a word in a document
func (ri *ReverseIndex) GetTFIDF(docID, word string, forwardIndex *ForwardIndex) float64 {
	tf := forwardIndex.GetTF(docID, word)
	idf := ri.GetIDF(word)
	return tf * idf
} 