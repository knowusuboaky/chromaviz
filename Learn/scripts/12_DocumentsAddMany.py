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



# Dummy document generation with overlapping content
documents = [
    {"id": "doc_1", "document": "The football team trained intensely for the upcoming match. The players are preparing to face their strongest opponents this season.", "metadata": {"source": "sports"}},
    {"id": "doc_2", "document": "The basketball game was thrilling. The team made an impressive comeback in the second half, winning the championship after a fierce battle.", "metadata": {"source": "sports"}},
    {"id": "doc_3", "document": "Technology is constantly evolving, and innovations like AI and machine learning are driving much of the progress in modern industries.", "metadata": {"source": "technology"}},
    {"id": "doc_4", "document": "The latest smartphone models feature cutting-edge AI capabilities, allowing for better image recognition and voice assistance.", "metadata": {"source": "technology"}},
    {"id": "doc_5", "document": "Artificial intelligence is reshaping how businesses approach problems, from customer service to data analysis and predictive maintenance.", "metadata": {"source": "technology"}},
    {"id": "doc_6", "document": "Good health is important for longevity, and exercise plays a vital role in maintaining a healthy body and mind. Regular physical activity improves cardiovascular health.", "metadata": {"source": "health"}},
    {"id": "doc_7", "document": "A balanced diet, rich in vegetables, proteins, and healthy fats, is key to staying in good shape. Health professionals recommend eating a variety of foods.", "metadata": {"source": "health"}},
    {"id": "doc_8", "document": "The integration of artificial intelligence in healthcare is revolutionizing diagnostics, treatment planning, and patient care management.", "metadata": {"source": "technology-health"}},
    {"id": "doc_9", "document": "AI-powered applications in healthcare are helping doctors diagnose diseases faster and with more accuracy, leading to better patient outcomes.", "metadata": {"source": "technology-health"}},
    {"id": "doc_10", "document": "The growing impact of technology on sports is evident in how teams use data analytics to optimize their performance and scout for talent.", "metadata": {"source": "sports-technology"}}
]



# Add the documents to the collection
document_texts = [doc["document"] for doc in documents]
document_ids = [doc["id"] for doc in documents]
document_metadatas = [doc["metadata"] for doc in documents]



pycollection.upsert(
    documents=document_texts,
    metadatas=document_metadatas,
    ids=document_ids
)

print("=============================================")
print("10 dummy documents added to the collection.")
print("=============================================")
