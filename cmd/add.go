package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// addCmd represents the add command
var addCmd = &cobra.Command{
	Use:   "add [file_path]",
	Short: "Add a document from a file path or all files in a directory",
	Long: `Add a document from a file path or all files in a directory.

Examples:
  docusearch add examples/sample_documents.txt
  docusearch add examples/
  docusearch add examples/sample_documents.txt --doc-id python_doc`,
	Args: cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		filePath := args[0]
		docID, _ := cmd.Flags().GetString("doc-id")
		storageFile, _ := cmd.Flags().GetString("storage-file")

		// Check if file path exists
		if _, err := os.Stat(filePath); os.IsNotExist(err) {
			fmt.Printf("Error: Path does not exist: %s\n", filePath)
			os.Exit(1)
		}

		store, err := loadStorage(storageFile, false)
		if err != nil {
			fmt.Printf("Error loading storage: %v\n", err)
			os.Exit(1)
		}

		info, err := os.Stat(filePath)
		if err != nil {
			fmt.Printf("Error accessing path: %v\n", err)
			os.Exit(1)
		}

		if info.IsDir() {
			if docID != "" {
				fmt.Println("Warning: --doc-id option is ignored when adding a directory")
			}

			docIDs, err := store.AddDocumentFromPath(filePath)
			if err != nil {
				fmt.Printf("Error adding documents: %v\n", err)
				os.Exit(1)
			}

			fmt.Printf("Added %d documents from directory\n", len(docIDs))
			for _, id := range docIDs {
				fmt.Printf("  - %s\n", id)
			}
		} else {
			if docID != "" {
				// Read file content and add with custom ID
				content, err := os.ReadFile(filePath)
				if err != nil {
					fmt.Printf("Error reading file: %v\n", err)
					os.Exit(1)
				}

				addedDocID := store.AddDocument(string(content), docID)
				fmt.Printf("Document added with ID: %s\n", addedDocID)
			} else {
				docIDs, err := store.AddDocumentFromPath(filePath)
				if err != nil {
					fmt.Printf("Error adding document: %v\n", err)
					os.Exit(1)
				}
				fmt.Printf("Document added with ID: %s\n", docIDs[0])
			}
		}

		if storageFile != "" {
			if err := saveStorage(store, storageFile, false); err != nil {
				fmt.Printf("Error saving storage: %v\n", err)
			} else {
				fmt.Printf("Storage saved to %s\n", storageFile)
			}
		}
	},
}

func init() {
	rootCmd.AddCommand(addCmd)

	addCmd.Flags().StringP("doc-id", "i", "", "Custom document ID (only for single files)")
	addCmd.Flags().StringP("storage-file", "s", "", "Storage file to load/save")
} 