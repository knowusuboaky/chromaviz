import chromadb
from chromadb.utils import embedding_functions
from datetime import datetime


CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection2"



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
        COLLECTION_NAME, embedding_function=pyEmbedFunction,
        metadata = {
		"uuid": "b573e65b-3e23-45c6-9129-9b8639f689d3",
            "modified_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": "description value",
            "embedding_model": "name of embedding model used, VERY helpful, critical in some cases",
            "embedding_model_version": "version of embedding model if not apparent in its name",
            "embedding_model_context_window": "research this manually, but all-MiniLM-L6-v2 is 512 tokens approx 250 words, the rest truncates",
            "language": "might be useful, use common shorthand version like en-GB, en-US etc.",
            "tags": "MUST, be, written, like, this, as, a, delimited, string, DOESN'T, accept, [tag,tag,tag]",
            "keywords": "MUST, be, written, as, a, delimited, string, DOESN'T, accept, nested, lists, like, [keyword,keyword,keyword]",
            "type": "something to describe a type or categorise it",
            "source": "something about the origin of the data it contains",
            "notes": "can be about anything, or even used as miscellaneous but related info",
            "version": "1.0"
        }
    )
    print(f"Created '{COLLECTION_NAME}' Successfully")
    print(f"===================================================")

