import chromadb
from chromadb.utils import embedding_functions

# Configuration variables
CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"

# Create a persistent Chroma client
persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)

# Initialize the embedding function
pyEmbedFunction = embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL)

# Retrieve all collections
allCollections = persistentChromaClient.list_collections()

# Count the collections
collectionCount = len(allCollections)

# Print the number of collections
print(f"Overview of All Collections:")
print(f"==========================================================================================")
print(f"Number of collections: {collectionCount}")
print(f"----------------------------------------")

# Optionally: Print the names, IDs, and document counts of the collections
if collectionCount > 0:
    for collection in allCollections:
        # Check if collection is valid before accessing it
        try:
            collection_name = collection.name
            collection_id = collection.id

            # Avoid trying to count documents in empty or corrupted collections
            if collection.count() is not None:
                document_count = collection.count()
                print(f"ID: {collection_id}   Name: {collection_name}   DocCount: {document_count}")
            else:
                print(f"ID: {collection_id}   Name: {collection_name}   DocCount: [Invalid]")

        except Exception as e:
            print(f"Error accessing collection {collection.name}: {str(e)}")
else:
    print("No collections found.")

# Print a closing line
print(f"==========================================================================================")
