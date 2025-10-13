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



# Prepare a list of documents to update
documents_to_update = [
    {"id": "doc_1", "document": "The football team is gearing up for the national championship game. They have been working hard and are excited about the opportunity.", "metadata": {"source": "sports", "updated": True}},
    {"id": "doc_2", "document": "The basketball team celebrated their recent victory in the tournament. Their teamwork and resilience led them to a strong finish.", "metadata": {"source": "sports", "updated": True}},
    {"id": "doc_3", "document": "The field of artificial intelligence continues to evolve rapidly, with new advancements in neural networks, data processing, and automation.", "metadata": {"source": "technology", "updated": True}},
    {"id": "doc_4", "document": "The newest smartphone models feature enhanced AI, enabling users to take better photos and make smarter decisions using voice commands.", "metadata": {"source": "technology", "updated": True}},
    {"id": "doc_5", "document": "The future of artificial intelligence lies in its integration into various industries. AI is helping businesses automate processes and improve customer service.", "metadata": {"source": "technology", "updated": True}},
    {"id": "doc_6", "document": "Maintaining a healthy lifestyle involves not only regular exercise but also managing stress and sleeping well. Mental health is as important as physical health.", "metadata": {"source": "health", "updated": True}},
    {"id": "doc_7", "document": "Eating a balanced diet is crucial for long-term health. It’s important to include a variety of foods in your diet to ensure you're getting all the necessary nutrients.", "metadata": {"source": "health", "updated": True}},
    {"id": "doc_8", "document": "AI is transforming healthcare by assisting doctors in diagnosing diseases earlier, predicting outcomes, and improving patient care strategies.", "metadata": {"source": "technology-health", "updated": True}},
    {"id": "doc_9", "document": "With advancements in machine learning, AI-powered healthcare applications are becoming more effective in managing patient health and predicting treatment responses.", "metadata": {"source": "technology-health", "updated": True}},
    {"id": "doc_10", "document": "Data analytics is revolutionizing the world of sports. Teams use performance data to strategize and recruit the best talent, making the sport more competitive.", "metadata": {"source": "sports-technology", "updated": True}},
]



# Update the documents in the collection
document_texts = [doc["document"] for doc in documents_to_update]
document_ids = [doc["id"] for doc in documents_to_update]
document_metadatas = [doc["metadata"] for doc in documents_to_update]



# Using the `update` method to update multiple documents at once
pycollection.update(
    documents=document_texts,
    metadatas=document_metadatas,
    ids=document_ids
)

print("===============================================")
print("Multiple documents updated in the collection.")
print("===============================================")
