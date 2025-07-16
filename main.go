package main

import (
	"fmt"
	"strings"

	"docusearch/pkg/storage"
)

func main() {
	fmt.Println("DocuSearch - In-memory Document Storage Library")
	fmt.Println(strings.Repeat("=", 50))

	// Create storage instance
	store := storage.New()

	// Add some sample documents
	fmt.Println("\nAdding sample documents...")

	doc1ID := store.AddDocument(
		"Python is a high-level programming language known for its simplicity and readability.",
		"python_doc",
	)

	doc2ID := store.AddDocument(
		"Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
		"ml_doc",
	)

	doc3ID := store.AddDocument(
		"Web development involves creating websites and web applications using various technologies.",
		"web_doc",
	)

	fmt.Printf("Added documents: %s, %s, %s\n", doc1ID, doc2ID, doc3ID)

	// Demonstrate search
	fmt.Println("\nSearching for 'python programming'...")
	results := store.Search("python programming", 3)

	for i, result := range results {
		fmt.Printf("%d. %s (score: %.4f)\n", i+1, result.DocID, result.Score)
		fmt.Printf("   Preview: %s\n", result.Preview)
	}

	// Demonstrate prefix search
	fmt.Println("\nPrefix search for 'prog'...")
	words := store.PrefixSearch("prog")
	fmt.Printf("Words starting with 'prog': %v\n", words)

	// Show statistics
	fmt.Println("\nStorage Statistics:")
	stats := store.GetStats()
	fmt.Printf("Total documents: %d\n", stats.TotalDocuments)
	fmt.Printf("Total unique words: %d\n", stats.TotalWords)

	fmt.Println("\nFor more features, use the CLI: docusearch --help")
} 