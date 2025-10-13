import chromadb
from chromadb.utils import embedding_functions


CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection2"



# Create a persistent Chroma client
persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)



# Initialize the embedding function
pyEmbedFunction = embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL)



# Delete the collection
try:
    # Try to retrieve the collection first to check if it exists
    pycollection = persistentChromaClient.get_collection(COLLECTION_NAME)

    # If the collection exists, delete it
    persistentChromaClient.delete_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' deleted successfully.")

except Exception as e:
    print(f"Error: Collection '{COLLECTION_NAME}' not found or couldn't be deleted. {e}")

