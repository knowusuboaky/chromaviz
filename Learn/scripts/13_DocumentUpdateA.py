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
    print(f"Collection {COLLECTION_NAME} found and retrieved.")

except Exception as e:
    print(f"Collection {COLLECTION_NAME} not found. Run the create collection script first")
    sys.exit()  # Exit the script




# If it gets this far, the Collection was Found, so its time to update the Document 
# Changing the text, and its metadata
test_document = {
    "id": "test_doc_1",
    "document": "changing all of the text so it should have an entirely different embedding. This is an amended document content but using the same document ID.",
    "metadata": {
        "uuid": "b573e65b-3e23-45c6-9129-9b8639f689d3",
        "hash": "e06e32ab-06ca-4aba-b3b1-99c0c622f868",
        "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "modified_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_extension": ".txt",
        "title": "title value",
        "description": "description value",
        "sentiment": "sentiment description here",
        "topic": "topic value",
        "authors": "author1, author2, author3",
        "doc_length": "integer count of all characters helps performance as a pre-calculation",
        "token_count": "tokens needed to make up the document useful to know for llm context sizes",
        "embedding_model": "name of embedding model used, VERY helpful, critical in some cases",
        "embedding_model_version": "version of embedding model if not apparent in its name",
        "language": "might be useful, use common shorthand version like en-GB, en-US etc.",
        "tags": "MUST, be, written, as, a, delimited, string, DOESN'T, accept, nested, lists, like, [tag,tag,tag]",
        "keywords": "MUST, be, written, as, a, delimited, string, DOESN'T, accept, nested, lists, like, [keyword,keyword,keyword]",
        "type": "something to describe a type or categorise it",
        "source": "something about the origin of the document",
        "notes": "can be about anything, or even used as miscellaneous but related info",
        "version": "1.0",
        "uri": "file:///c:/temp/example/path"
    }
}

pycollection.update(
    documents=[test_document["document"]],
    metadatas=[test_document["metadata"]],
    ids=[test_document["id"]]
)
print("==========================================")
print("Test document Updated in the collection.")
print("==========================================")



