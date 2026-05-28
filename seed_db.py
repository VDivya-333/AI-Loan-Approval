from chroma_store import add_document

print("Seeding ChromaDB with an initial document...")

add_document(
    application_id=0,
    doc_id="seed_doc_1",
    text="This is a valid payslip document text.",
    metadata={"type": "income_proof", "source": "seed_data"}
)
print("Seeding complete.")