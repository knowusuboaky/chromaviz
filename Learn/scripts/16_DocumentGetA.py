import chromadb
from chromadb.utils import embedding_functions
import sys


# Define variables
CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection1"



# The specific document ID you want to fetch
TARGET_DOC_ID = "test_doc_1"



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



# Fetch all the documents and their embeddings
results = pycollection.get(include=["embeddings", "documents"])



# Find the document with the specific ID
doc_found = False
for i, doc_id in enumerate(results['ids']):
    if doc_id == TARGET_DOC_ID:
        embedding = results['embeddings'][i]
        document = results['documents'][i]
        print(f"---------------------------------------------------------------------")
        print(f"ID: {doc_id}")
        print(f"")
        print(f"Document:\n{document}")
        print(f"")
        print(f"Embedding:\n{embedding}")
        print(f"---------------------------------------------------------------------")
        doc_found = True
        break


# If the document ID was not found
if not doc_found:
    print(f"===============================================================")
    print(f"Document with ID '{TARGET_DOC_ID}' not found in the collection.")
    print(f"===============================================================")