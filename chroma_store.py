import chromadb

client = chromadb.PersistentClient(path="chroma")

def add_document(application_id, text, doc_id=None, metadata=None):
    collection = client.get_or_create_collection(name="loan_docs")
    # Use a combination of app_id and doc_id for a unique primary key
    collection.add(
        documents=[text],
        metadatas=[metadata or {}],
        ids=[f"app_{application_id}_{doc_id or 'doc'}"]
    )

def fetch_similar(content):
    collection = client.get_or_create_collection(name="loan_docs")
    result = collection.query(query_texts=[content], n_results=1)
    return result
