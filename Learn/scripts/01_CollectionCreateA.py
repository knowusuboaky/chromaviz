import chromadb
from chromadb.utils import embedding_functions


CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection1"



# Create a persistent Chroma client
persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)



# Initialize the embedding function
pyEmbedFunction = embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL)



# Create the Collection if it doesnt exist, otherwise, get the collection, and assign the Embedding Function to it
# Using this method, rather than get_or_create_collection, because that doesn't accept an embedding function argument, but .get and .create both do. 
try:
    pycollection = persistentChromaClient.get_collection(
        COLLECTION_NAME, embedding_function=pyEmbedFunction
    )
    print(f"===================================================")
    print(f"Existing Collection '{COLLECTION_NAME}' found.")
    print(f"===================================================")

except Exception as e:
    print(f"===================================================")
    print(f"Collection '{COLLECTION_NAME}' not found. Creating a new one...")
    pycollection = persistentChromaClient.create_collection(
        COLLECTION_NAME, embedding_function=pyEmbedFunction
    )
    print(f"Created '{COLLECTION_NAME}' Successfully")
    print(f"===================================================")


