package trie

import (
	"strings"
)

// TrieNode represents a node in the trie data structure
type TrieNode struct {
	children            map[rune]*TrieNode
	isEndOfWord         bool
	word                string
	containingDocuments map[string]bool
	docToWordCount      map[string]int
}

// NewTrieNode creates a new trie node
func NewTrieNode() *TrieNode {
	return &TrieNode{
		children:            make(map[rune]*TrieNode),
		isEndOfWord:         false,
		word:                "",
		containingDocuments: make(map[string]bool),
		docToWordCount:      make(map[string]int),
	}
}

// Trie represents a trie data structure for efficient prefix searching with document mappings
type Trie struct {
	root *TrieNode
}

// New creates a new trie instance
func New() *Trie {
	return &Trie{
		root: NewTrieNode(),
	}
}

// Insert adds a word to the trie
func (t *Trie) Insert(word string) {
	node := t.root
	word = strings.ToLower(word)

	for _, char := range word {
		if _, exists := node.children[char]; !exists {
			node.children[char] = NewTrieNode()
		}
		node = node.children[char]
	}

	node.isEndOfWord = true
	node.word = word
}

// AddDocumentToWord adds a document to a word's document set
func (t *Trie) AddDocumentToWord(word, docID string, count int) {
	node := t.findNode(strings.ToLower(word))
	if node != nil && node.isEndOfWord {
		node.containingDocuments[docID] = true
		node.docToWordCount[docID] = count
	}
}

// RemoveDocumentFromWord removes a document from a word's document set
func (t *Trie) RemoveDocumentFromWord(word, docID string) bool {
	node := t.findNode(strings.ToLower(word))
	if node != nil && node.isEndOfWord {
		if _, exists := node.containingDocuments[docID]; exists {
			delete(node.containingDocuments, docID)
			delete(node.docToWordCount, docID)
			return true
		}
	}
	return false
}

// GetDocumentsForWord returns all documents containing a word and their counts
func (t *Trie) GetDocumentsForWord(word string) map[string]int {
	node := t.findNode(strings.ToLower(word))
	if node != nil && node.isEndOfWord {
		result := make(map[string]int)
		for docID, count := range node.docToWordCount {
			result[docID] = count
		}
		return result
	}
	return make(map[string]int)
}

// GetDocumentFrequency returns the number of documents containing a word
func (t *Trie) GetDocumentFrequency(word string) int {
	node := t.findNode(strings.ToLower(word))
	if node != nil && node.isEndOfWord {
		return len(node.containingDocuments)
	}
	return 0
}

// Search looks for an exact word in the trie
func (t *Trie) Search(word string) bool {
	node := t.findNode(strings.ToLower(word))
	return node != nil && node.isEndOfWord
}

// StartsWith finds all words that start with the given prefix
func (t *Trie) StartsWith(prefix string) []string {
	node := t.findNode(strings.ToLower(prefix))
	if node == nil {
		return []string{}
	}

	var words []string
	t.collectWords(node, &words)
	return words
}

// GetDocumentsForPrefix returns all documents containing words that start with the given prefix
func (t *Trie) GetDocumentsForPrefix(prefix string) map[string]int {
	node := t.findNode(strings.ToLower(prefix))
	if node == nil {
		return make(map[string]int)
	}

	docCounts := make(map[string]int)
	t.collectDocumentsFromNode(node, docCounts)
	return docCounts
}

// findNode finds the node corresponding to the given prefix
func (t *Trie) findNode(prefix string) *TrieNode {
	node := t.root
	for _, char := range prefix {
		if child, exists := node.children[char]; exists {
			node = child
		} else {
			return nil
		}
	}
	return node
}

// collectWords collects all words from the given node and its descendants
func (t *Trie) collectWords(node *TrieNode, words *[]string) {
	if node.isEndOfWord && node.word != "" {
		*words = append(*words, node.word)
	}

	for _, child := range node.children {
		t.collectWords(child, words)
	}
}

// collectDocumentsFromNode collects all documents from the given node and its descendants
func (t *Trie) collectDocumentsFromNode(node *TrieNode, docCounts map[string]int) {
	if node.isEndOfWord {
		for docID, count := range node.docToWordCount {
			docCounts[docID] += count
		}
	}

	for _, child := range node.children {
		t.collectDocumentsFromNode(child, docCounts)
	}
}

// Remove removes a word from the trie (only if no documents contain it)
func (t *Trie) Remove(word string) bool {
	node := t.findNode(strings.ToLower(word))
	if node != nil && node.isEndOfWord && len(node.containingDocuments) == 0 {
		return t.removeHelper(t.root, strings.ToLower(word), 0)
	}
	return false
}

// removeHelper is a helper method to remove a word from the trie
func (t *Trie) removeHelper(node *TrieNode, word string, index int) bool {
	if index == len([]rune(word)) {
		if !node.isEndOfWord {
			return false
		}
		node.isEndOfWord = false
		node.word = ""
		return len(node.children) == 0
	}

	chars := []rune(word)
	char := chars[index]
	child, exists := node.children[char]
	if !exists {
		return false
	}

	shouldDeleteChild := t.removeHelper(child, word, index+1)

	if shouldDeleteChild {
		delete(node.children, char)
		return len(node.children) == 0 && !node.isEndOfWord
	}

	return false
}

// GetAllWords returns all words stored in the trie
func (t *Trie) GetAllWords() []string {
	var words []string
	t.collectWords(t.root, &words)
	return words
}

// CleanupEmptyWords removes words that have no documents
func (t *Trie) CleanupEmptyWords() {
	wordsToRemove := []string{}
	for _, word := range t.GetAllWords() {
		node := t.findNode(word)
		if node != nil && len(node.containingDocuments) == 0 {
			wordsToRemove = append(wordsToRemove, word)
		}
	}

	for _, word := range wordsToRemove {
		t.Remove(word)
	}
} 