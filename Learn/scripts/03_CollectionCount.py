import chromadb
from chromadb.utils import embedding_functions


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
print(f"========================================")
print(f"Number of collections: {collectionCount}")



# Optionally: Print the names of the collections
if collectionCount > 0:
    print(f"----------------------------------------")
    for collection in allCollections:
        print(collection.name)
else:
    print("No collections found.")


# Print a closing Line
print(f"========================================")