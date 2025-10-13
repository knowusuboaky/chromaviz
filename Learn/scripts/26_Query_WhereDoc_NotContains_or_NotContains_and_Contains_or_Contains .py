import chromadb
from chromadb.utils import embedding_functions



# Configuration for ChromaDB
CHROMA_DATA_PATH = "C:\\Program Files\\ChromaDB\\Data\\TestDB"
EMBEDMODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "testCollection1"



# =========================================================================
# Define a query, and a number of results to return 
query_text = "sport"

# Define the number of results to return 
num_of_returned_results = 10

# Define filter strings
document_filter_string_1 = "technology"
document_filter_string_2 = "health"
document_filter_string_3 = "team"
document_filter_string_4 = "game"
# =========================================================================




# Create a persistent Chroma client
persistentChromaClient = chromadb.PersistentClient(path=CHROMA_DATA_PATH)



# Initialize the embedding function
pyEmbedFunction = embedding_functions.SentenceTransformerEmbeddingFunction(EMBEDMODEL)



# Get the Collection and assign the Embedding Function to it
try:
    pycollection = persistentChromaClient.get_collection(
        COLLECTION_NAME, embedding_function=pyEmbedFunction
    )
    print(f"Collection {COLLECTION_NAME} found and retrieved.")
except Exception as e:
    print(f"Collection {COLLECTION_NAME} not found. Run the create collection script first.")
    exit()






# Perform a vector search for the most similar documents in the collection using the query text
# ==============================================================================================
# Complex and specifc filtering:
# filter on documents PLAIN text whether it contains BOTH - something from string1 or string2, AND something from string5, string6, string7, or string8
# also filter on metadata where EITHER, the title contains test AND is shorter than 500 tokens, OR, the title contains live AND is longer than 500 tokens
# ==============================================================================================

results = pycollection.query(
    query_texts=[query_text],
    n_results=num_of_returned_results,
    where_document={
        "$and": [
            {"$or": [{"$not_contains": document_filter_string_1}, {"$not_contains": document_filter_string_2}]},
            {"$or": [{"$contains": document_filter_string_3}, {"$contains": document_filter_string_4}]}
        ]
    }
)





# TECHNICALLY all you need to see the results is this, 
# just uncomment the line below, it and delete everything else after it 
# print(f"{results}")





# OR, keep the above line commented out
# and keep the below, to beautify the output in the console and make it easily readable

# Beautify and print the results
print("")
print("=" * 60)
print("Number of Results to Return: ", num_of_returned_results)
print("\nUsers Query:\n", query_text)
print("\n")



# Storing each array into temporary variables as they're lists nested in lists
tempScoreArray = results['distances'][0]  # Flatten the first list in the 'distances' array
tempIdArray = results['ids'][0]  # Flatten the first list in the 'ids' array
tempDocumentArray = results['documents'][0]  # Flatten the first list in the 'documents' array
tempMetadataArray = results['metadatas'][0]  # Flatten the first list in the 'metadatas' array



# Loop through the length of one of the arrays (assuming all arrays are the same length)
for i in range(len(tempScoreArray)):
    print("-" * 60)
    print(f"Result {i + 1}     Score: {tempScoreArray[i]}")
    print("-" * 60)
    
    # For each result, print the corresponding values in a readable format
    print(f"ID:       {tempIdArray[i]}")
    print(f"Metadata: {tempMetadataArray[i]}")
    print(f"")
    print(f"Document:\n{tempDocumentArray[i]}")
    
    print("\n\n")

print("=" * 60)