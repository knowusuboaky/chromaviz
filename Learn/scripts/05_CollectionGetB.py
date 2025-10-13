import chromadb
from chromadb.utils import embedding_functions
import json  # To prettify the output



# Configuration variables
CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection2"



# Create a persistent Chroma client
persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)



# Initialize the embedding function
pyEmbedFunction = embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL)



# Fetch the collection
coll = persistentChromaClient.get_collection(COLLECTION_NAME)




# Print basic collection information
print(f"Getting Collection")
print(f"==============================================================")
print(f" ID:        {coll.id}")
print(f" Name:      {coll.name}")
print(f" tenant:    {coll.tenant}")
print(f" database:  {coll.database}")
print(f"--------------------------------------------------------------")
print(f"Metadata: {coll.metadata}")
print(f"--------------------------------------------------------------")



# Print Collections Configuration
print(f"Configuration:")
print(json.dumps(coll.configuration_json, indent=4))  # Pretty print the JSON configuration



# Optionally, print collection's index if available
print(f"--------------------------------------------------------------")
# Fetch all documents in the collection
documents = coll.get()

# Pretty print the document structure
print(f"Documents:")
print(json.dumps(documents, indent=4))  # Pretty print the document structure
print(f"==============================================================")