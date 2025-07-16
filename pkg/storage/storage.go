package storage

import (
	"encoding/json"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"unicode"

	"docusearch/pkg/index"
	"docusearch/pkg/trie"
	"github.com/google/uuid"
)

// DocumentInfo represents information about a document
type DocumentInfo struct {
	DocID       string            `json:"doc_id"`
	Content     string            `json:"content"`
	WordCounts  map[string]int    `json:"word_counts"`
	TotalWords  int               `json:"total_words"`
	UniqueWords int               `json:"unique_words"`
}

// Stats represents storage statistics
type Stats struct {
	TotalDocuments        int `json:"total_documents"`
	TotalWords           int `json:"total_words"`
	TotalDocumentsInIndex int `json:"total_documents_in_index"`
}

// SearchResult represents a search result
type SearchResult struct {
	DocID   string  `json:"doc_id"`
	Score   float64 `json:"score"`
	Preview string  `json:"preview"`
}

// StorageData represents the serializable data for persistence
type StorageData struct {
	Documents      map[string]string            `json:"documents"`
	TotalDocuments int                          `json:"total_documents"`
	ForwardIndex   ForwardIndexData             `json:"forward_index"`
}

// ForwardIndexData represents the serializable forward index data
type ForwardIndexData struct {
	Documents  map[string]map[string]int `json:"documents"`
	DocLengths map[string]int            `json:"doc_lengths"`
}

// DocumentStorage provides in-memory document storage with TF-IDF search capabilities
type DocumentStorage struct {
	trie           *trie.Trie
	forwardIndex   *index.ForwardIndex
	docIDToDocument map[string]string
	totalDocuments int
}

// generateDocID generates a unique document ID
func generateDocID() string {
	return fmt.Sprintf("doc_%s", uuid.New().String())
}

// New creates a new DocumentStorage instance
func New() *DocumentStorage {
	return &DocumentStorage{
		trie:           trie.New(),
		forwardIndex:   index.NewForwardIndex(),
		docIDToDocument: make(map[string]string),
		totalDocuments: 0,
	}
}

// NewWithData creates a DocumentStorage instance with existing data
func NewWithData(documents map[string]string, totalDocuments int, forwardIndexData *index.ForwardIndex) *DocumentStorage {
	storage := &DocumentStorage{
		trie:           trie.New(),
		forwardIndex:   forwardIndexData,
		docIDToDocument: documents,
		totalDocuments: totalDocuments,
	}

	// Rebuild trie from forward index
	for docID, wordCounts := range forwardIndexData.GetDocuments() {
		for word, count := range wordCounts {
			if !storage.trie.Search(word) {
				storage.trie.Insert(word)
			}
			storage.trie.AddDocumentToWord(word, docID, count)
		}
	}

	return storage
}

// AddDocumentFromPath adds a document from a file path or all files in a directory
func (ds *DocumentStorage) AddDocumentFromPath(filePath string) ([]string, error) {
	info, err := os.Stat(filePath)
	if err != nil {
		return nil, fmt.Errorf("path not found: %s", filePath)
	}

	if info.IsDir() {
		return ds.addDirectory(filePath)
	} else {
		docID, err := ds.addSingleFile(filePath)
		if err != nil {
			return nil, err
		}
		return []string{docID}, nil
	}
}

// addSingleFile adds a single file to the storage
func (ds *DocumentStorage) addSingleFile(filePath string) (string, error) {
	content, err := ds.readFileContent(filePath)
	if err != nil {
		return "", err
	}

	return ds.AddDocument(content, filePath), nil
}

// readFileContent reads file content with fallback encoding
func (ds *DocumentStorage) readFileContent(filePath string) (string, error) {
	data, err := os.ReadFile(filePath)
	if err != nil {
		return "", err
	}

	// Try UTF-8 first, then fallback to Latin-1 equivalent
	content := string(data)
	if !isValidUTF8(content) {
		// For Go, we'll just use the bytes as-is since Go handles encoding more gracefully
		content = string(data)
	}

	return content, nil
}

// isValidUTF8 checks if the string is valid UTF-8
func isValidUTF8(s string) bool {
	for _, r := range s {
		if r == unicode.ReplacementChar {
			return false
		}
	}
	return true
}

// addDirectory adds all files in a directory to the storage
func (ds *DocumentStorage) addDirectory(dirPath string) ([]string, error) {
	var addedDocs []string

	textExtensions := map[string]bool{
		".txt": true, ".md": true, ".py": true, ".js": true, ".html": true,
		".css": true, ".json": true, ".xml": true, ".csv": true, ".tsv": true,
		".log": true, ".rst": true, ".tex": true, ".adoc": true, ".org": true,
		".go": true, // Adding Go files since this is a Go project
	}

	err := filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		ext := strings.ToLower(filepath.Ext(path))
		if textExtensions[ext] {
			docID, err := ds.addSingleFile(path)
			if err != nil {
				fmt.Printf("Warning: Could not add %s: %v\n", path, err)
				return nil // Continue processing other files
			}
			addedDocs = append(addedDocs, docID)
		}

		return nil
	})

	return addedDocs, err
}

// AddDocument adds a document with given content
func (ds *DocumentStorage) AddDocument(content, docID string) string {
	if docID == "" {
		docID = generateDocID()
	} else if _, exists := ds.docIDToDocument[docID]; exists {
		panic(fmt.Sprintf("Document with ID %s already exists", docID))
	}

	wordCounts := ds.tokenize(content)
	ds.docIDToDocument[docID] = content
	ds.forwardIndex.AddDocument(docID, wordCounts)

	for word, count := range wordCounts {
		if !ds.trie.Search(word) {
			ds.trie.Insert(word)
		}
		ds.trie.AddDocumentToWord(word, docID, count)
	}

	ds.totalDocuments++
	return docID
}

// RemoveDocument removes a document from storage
func (ds *DocumentStorage) RemoveDocument(docID string) bool {
	if _, exists := ds.docIDToDocument[docID]; !exists {
		return false
	}

	wordCounts := ds.forwardIndex.GetDocumentWords(docID)
	ds.forwardIndex.RemoveDocument(docID)

	for word := range wordCounts {
		ds.trie.RemoveDocumentFromWord(word, docID)
	}

	delete(ds.docIDToDocument, docID)
	ds.trie.CleanupEmptyWords()

	if ds.totalDocuments > 0 {
		ds.totalDocuments--
	}

	return true
}

// Search performs TF-IDF search for documents
func (ds *DocumentStorage) Search(query string, topK int) []SearchResult {
	queryWords := ds.tokenizeQuery(strings.ToLower(query))
	if len(queryWords) == 0 {
		return []SearchResult{}
	}

	docScores := make(map[string]float64)

	for _, word := range queryWords {
		docsWithWord := ds.trie.GetDocumentsForWord(word)

		for docID := range docsWithWord {
			tfIdf := ds.calculateTFIDF(docID, word)
			docScores[docID] += tfIdf
		}
	}

	// Sort documents by score
	type docScore struct {
		docID string
		score float64
	}

	var sortedDocs []docScore
	for docID, score := range docScores {
		sortedDocs = append(sortedDocs, docScore{docID, score})
	}

	sort.Slice(sortedDocs, func(i, j int) bool {
		return sortedDocs[i].score > sortedDocs[j].score
	})

	// Build results
	var results []SearchResult
	limit := topK
	if limit > len(sortedDocs) {
		limit = len(sortedDocs)
	}

	for i := 0; i < limit; i++ {
		docID := sortedDocs[i].docID
		score := sortedDocs[i].score
		content := ds.docIDToDocument[docID]
		preview := ds.getContentPreview(content, queryWords, 200)
		
		results = append(results, SearchResult{
			DocID:   docID,
			Score:   score,
			Preview: preview,
		})
	}

	return results
}

// SearchByPrefix searches for documents using prefix matching on query terms
func (ds *DocumentStorage) SearchByPrefix(prefix string, topK int) []SearchResult {
	if strings.TrimSpace(prefix) == "" {
		return []SearchResult{}
	}

	docsWithPrefix := ds.trie.GetDocumentsForPrefix(strings.ToLower(prefix))
	if len(docsWithPrefix) == 0 {
		return []SearchResult{}
	}

	docScores := make(map[string]float64)

	for docID, totalCount := range docsWithPrefix {
		docLength := ds.forwardIndex.GetDocumentLength(docID)
		if docLength > 0 {
			docScores[docID] = float64(totalCount) / float64(docLength)
		}
	}

	// Sort by score
	type docScore struct {
		docID string
		score float64
	}

	var sortedDocs []docScore
	for docID, score := range docScores {
		sortedDocs = append(sortedDocs, docScore{docID, score})
	}

	sort.Slice(sortedDocs, func(i, j int) bool {
		return sortedDocs[i].score > sortedDocs[j].score
	})

	// Build results
	var results []SearchResult
	limit := topK
	if limit > len(sortedDocs) {
		limit = len(sortedDocs)
	}

	for i := 0; i < limit; i++ {
		docID := sortedDocs[i].docID
		score := sortedDocs[i].score
		content := ds.docIDToDocument[docID]
		preview := ds.getContentPreview(content, []string{prefix}, 200)
		
		results = append(results, SearchResult{
			DocID:   docID,
			Score:   score,
			Preview: preview,
		})
	}

	return results
}

// PrefixSearch searches for words that start with the given prefix
func (ds *DocumentStorage) PrefixSearch(prefix string) []string {
	return ds.trie.StartsWith(prefix)
}

// GetDocumentInfo gets information about a specific document
func (ds *DocumentStorage) GetDocumentInfo(docID string) *DocumentInfo {
	content, exists := ds.docIDToDocument[docID]
	if !exists {
		return nil
	}

	wordCounts := ds.forwardIndex.GetDocumentWords(docID)
	docLength := ds.forwardIndex.GetDocumentLength(docID)

	return &DocumentInfo{
		DocID:       docID,
		Content:     content,
		WordCounts:  wordCounts,
		TotalWords:  docLength,
		UniqueWords: len(wordCounts),
	}
}

// GetStats gets statistics about the document storage
func (ds *DocumentStorage) GetStats() Stats {
	return Stats{
		TotalDocuments:        len(ds.docIDToDocument),
		TotalWords:           len(ds.trie.GetAllWords()),
		TotalDocumentsInIndex: ds.totalDocuments,
	}
}

// SmartSearch automatically chooses between exact and prefix search
func (ds *DocumentStorage) SmartSearch(query string, topK int) []SearchResult {
	if strings.TrimSpace(query) == "" {
		return []SearchResult{}
	}

	// Handle escaped asterisks
	query = strings.ReplaceAll(query, "\\*", "___ESCAPED_ASTERISK___")

	if strings.HasSuffix(query, "*") {
		prefix := strings.TrimSpace(strings.TrimSuffix(query, "*"))
		if prefix != "" {
			return ds.SearchByPrefix(prefix, topK)
		}
		return []SearchResult{}
	}

	// Restore escaped asterisks
	query = strings.ReplaceAll(query, "___ESCAPED_ASTERISK___", "*")

	return ds.Search(query, topK)
}

// calculateTFIDF calculates TF-IDF score for a word in a document
func (ds *DocumentStorage) calculateTFIDF(docID, word string) float64 {
	tf := ds.forwardIndex.GetTF(docID, word)
	docFreq := ds.trie.GetDocumentFrequency(word)
	if docFreq == 0 {
		return 0
	}
	idf := math.Log2(float64(ds.totalDocuments+1)/float64(docFreq+1)) + 1

	return tf * idf
}

// tokenize tokenizes text into words
func (ds *DocumentStorage) tokenize(text string) map[string]int {
	wordRegex := regexp.MustCompile(`\b[a-zA-Z]+\b`)
	words := wordRegex.FindAllString(strings.ToLower(text), -1)
	
	wordCounts := make(map[string]int)
	for _, word := range words {
		if len(word) > 1 { // Only include words longer than 1 character
			wordCounts[word]++
		}
	}
	
	return wordCounts
}

// tokenizeQuery tokenizes query text into words
func (ds *DocumentStorage) tokenizeQuery(text string) []string {
	wordRegex := regexp.MustCompile(`\b[a-zA-Z]+\b`)
	words := wordRegex.FindAllString(text, -1)
	
	var result []string
	for _, word := range words {
		if len(word) > 1 {
			result = append(result, word)
		}
	}
	
	return result
}

// getContentPreview generates a preview of the content highlighting query words
func (ds *DocumentStorage) getContentPreview(content string, queryWords []string, maxLength int) string {
	if len(content) <= maxLength {
		return content
	}

	contentLower := strings.ToLower(content)
	firstPos := len(content)

	for _, word := range queryWords {
		pos := strings.Index(contentLower, word)
		if pos != -1 && pos < firstPos {
			firstPos = pos
		}
	}

	start := 0
	if firstPos < len(content) {
		start = firstPos - 50
		if start < 0 {
			start = 0
		}
	}

	end := start + maxLength
	if end > len(content) {
		end = len(content)
	}

	preview := content[start:end]

	if start > 0 {
		preview = "..." + preview
	}
	if end < len(content) {
		preview = preview + "..."
	}

	return preview
}

// Save saves the storage to a JSON file
func (ds *DocumentStorage) Save(filePath string) error {
	data := StorageData{
		Documents:      ds.docIDToDocument,
		TotalDocuments: ds.totalDocuments,
		ForwardIndex: ForwardIndexData{
			Documents:  ds.forwardIndex.GetDocuments(),
			DocLengths: ds.forwardIndex.GetDocLengths(),
		},
	}

	file, err := os.Create(filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	return encoder.Encode(data)
}

// Load loads storage from a JSON file
func Load(filePath string) (*DocumentStorage, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return nil, err
	}

	var storageData StorageData
	if err := json.Unmarshal(data, &storageData); err != nil {
		return nil, err
	}

	forwardIndex := index.NewForwardIndexWithData(
		storageData.ForwardIndex.Documents,
		storageData.ForwardIndex.DocLengths,
	)

	storage := NewWithData(
		storageData.Documents,
		storageData.TotalDocuments,
		forwardIndex,
	)

	return storage, nil
} 