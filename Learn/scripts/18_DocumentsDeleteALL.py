import chromadb
from chromadb.utils import embedding_functions
import sys



CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection1"



# Create a persistent Chroma client
persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)



# Initialize the embedding function
pyEmbedFunction = embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL)



# Get the Collection and assign the Embedding Function to it
# Otherwise, Abort Script 
try:
    pycollection = persistentChromaClient.get_collection(
        COLLECTION_NAME, embedding_function=pyEmbedFunction
    )
    print(f"Existing Collection {COLLECTION_NAME} found.")

except Exception as e:
    print(f"Collection {COLLECTION_NAME} not found. Run the create collection script first")
    sys.exit()  # Exit the script




# Check if the collection is empty, if so, abort script 
if pycollection.count() == 0:
    print(f"===================================================================")
    print(f"No documents found in collection {COLLECTION_NAME}.")
    print(f"Aborting script.")
    print(f"===================================================================")
    sys.exit()



# Fetch all document IDs in the collection
results = pycollection.get(include=["documents"])



# Extract the document IDs
doc_ids_to_delete = results['ids']



# If there are any documents, delete them
if doc_ids_to_delete:
    pycollection.delete(ids=doc_ids_to_delete)
    print(f"==================================================================")
    print(f"All documents in collection '{COLLECTION_NAME}' have been deleted.")
    print(f"==================================================================")

else:
    print(f"==================================================================")
    print(f"No documents found to delete in collection '{COLLECTION_NAME}'.")
    print(f"==================================================================")