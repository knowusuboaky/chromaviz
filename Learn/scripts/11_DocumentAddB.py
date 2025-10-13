import chromadb
from chromadb.utils import embedding_functions
import sys
from datetime import datetime



CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection2"



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
    print(f"Collection {COLLECTION_NAME} found and retrieved.")

except Exception as e:
    print(f"Collection {COLLECTION_NAME} not found. Run the create collection script first")
    sys.exit()  # Exit the script




# If it gets this far, the Collection was Found, so its time to add Documents 
test_document = {
    "id": "test_doc_99",
    "document": "This is a test document for checking the collection with URI and Metadata.",
    "metadata": {
        "uuid": "b573e65b-3e23-45c6-9129-9b8639f689d3",
        "hash": "e06e32ab-06ca-4aba-b3b1-99c0c622f868",
        "code": "12345",
        "modified_date": "2024-12-11 12:34:56",
        "file_name": "MyDocument.txt",
        "file_extension": ".txt",
        "title": "title value",
        "description": "description value",
        "sentiment": "sentiment description here",
        "topic": "topic value",
        "authors": "author1, author2, author3",
        "doc_length": "integer count of all characters helps performance as a per-calculation",
        "chunk_total": 100,
        "chunk_num": 1,
        "token_count": "tokens needed to make up the document useful to know for LLM context sizes",
        "embedding_model": "name of embedding model used, VERY helpful, critical in some cases",
        "embedding_model_version": "version of embedding model if not apparent in its name",
        "language": "might be useful, use common shorthand version like en-GB, en-US etc.",
        "tags": "MUST, be, written, as, a, delimited, string, DOESN'T, accept, nested, lists, like, [tag,tag,tag]",
        "keywords": "MUST, be, written, as, a, delimited, string, DOESN'T, accept, nested, lists, like, [keyword,keyword,keyword]",
        "type": "something to describe a type or categorize it",
        "source": "something about the origin of the document",
        "notes": "can be about anything, or even used as miscellaneous but related info",
        "version": "1.0",
        "uri": "file:///c:/temp/example/path"
    }
}



# Add Document to the Collection
pycollection.add(
    documents=[test_document["document"]],
    metadatas=[test_document["metadata"]],
    ids=[test_document["id"]]
)

print("======================================")
print("Test document added to the collection.")
print("======================================")



