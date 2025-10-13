import chromadb
from chromadb.utils import embedding_functions


CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"



# Create a persistent Chroma client
persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)



# Initialize the embedding function
pyEmbedFunction = embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL)



# Delete ALL Collections
print(f"Deleting ALL Collections...")

try:
    # Retrieve all collections (this returns a list of Collection objects)
    collections = persistentChromaClient.list_collections()

    if collections:
        # Iterate through and delete each collection by name
        print(f"=========================================================")
        for collection in collections:
            collection_name = collection.name  # Extract the collection name
            persistentChromaClient.delete_collection(collection_name)
            print(f"Collection '{collection_name}' deleted successfully.")
        print(f"=========================================================")

    else:
        print(f"========================================")
        print("No collections found to delete.")
        print(f"========================================")
        
except Exception as e:
    print(f"========================================")
    print(f"Error: Could not delete collections. {e}")
    print(f"========================================")
