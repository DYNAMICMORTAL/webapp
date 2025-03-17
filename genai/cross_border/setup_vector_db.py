import os
import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import os
import dotenv

dotenv.load_dotenv()

def setup_vector_db():
    """
    Set up a ChromaDB vector database with knowledge base documents
    using Google Generative AI embeddings.
    """
    # Initialize Google Generative AI embeddings
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Get the knowledge base directory path
    kb_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
    
    # Define the vector DB path
    vector_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_db")
    
    # Create documents from knowledge base files
    documents = []
    
    # Process each file in the knowledge base directory
    for filename in os.listdir(kb_dir):
        if filename.endswith(".md"):
            file_path = os.path.join(kb_dir, filename)
            
            # Extract category from filename
            category = filename.replace(".md", "")
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Split content into chunks (approximately 1000 characters each)
                # This helps with more granular retrieval
                chunk_size = 1000
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                
                for i, chunk in enumerate(chunks):
                    # Create a document with metadata
                    doc = Document(
                        page_content=chunk,
                        metadata={
                            "source": filename,
                            "category": category,
                            "chunk_id": i
                        }
                    )
                    documents.append(doc)
    
    # Create or load the vector store
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=vector_db_path
    )
    
    # Persist the vector store
    vector_store.persist()
    
    print(f"Vector database created with {len(documents)} documents")
    return vector_store

if __name__ == "__main__":
    setup_vector_db()