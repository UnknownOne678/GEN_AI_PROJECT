"""
Document Loader and Processing Module
"""
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.core.config import (
    DOCUMENT_DIRECTORY,
    VECTOR_STORE_DIRECTORY,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL
)


def load_documents(doc_directory: str = DOCUMENT_DIRECTORY) -> list:
    """
    Load all PDF and TXT files from the specified directory.
    
    Args:
        doc_directory: Path to directory containing document files
        
    Returns:
        List of Document objects from all files
    """
    doc_path = Path(doc_directory)
    if not doc_path.exists():
        os.makedirs(doc_path, exist_ok=True)
        print(f"Created document directory at: {doc_path}")
        return []
        
    all_documents = []
    
    # Load PDFs
    pdf_files = list(doc_path.glob("*.pdf"))
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF file(s).")
        for pdf_file in pdf_files:
            try:
                print(f"Loading: {pdf_file.name}")
                loader = PyPDFLoader(str(pdf_file))
                documents = loader.load()
                # Add metadata
                for doc in documents:
                    doc.metadata['source'] = pdf_file.name
                    doc.metadata['type'] = 'pdf'
                all_documents.extend(documents)
            except Exception as e:
                print(f"Error loading {pdf_file.name}: {e}")

    # Load TXTs
    txt_files = list(doc_path.glob("*.txt"))
    if txt_files:
        print(f"Found {len(txt_files)} TXT file(s).")
        for txt_file in txt_files:
            try:
                print(f"Loading: {txt_file.name}")
                loader = TextLoader(str(txt_file), encoding='utf-8')
                documents = loader.load()
                # Add metadata
                for doc in documents:
                    doc.metadata['source'] = txt_file.name
                    doc.metadata['type'] = 'txt'
                all_documents.extend(documents)
            except Exception as e:
                print(f"Error loading {txt_file.name}: {e}")
    
    if not all_documents:
        print(f"No documents found in '{doc_directory}'.")
    else:
        print(f"Successfully loaded {len(all_documents)} chunks/pages.")
        
    return all_documents


def split_documents(documents: list, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list:
    """
    Split documents into smaller chunks for better retrieval.
    
    Args:
        documents: List of Document objects
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of split Document chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split documents into {len(chunks)} chunks.")
    return chunks


def create_vector_store(chunks: list, persist_directory: str = VECTOR_STORE_DIRECTORY, force_recreate: bool = False):
    """
    Create or load a vector store from document chunks.
    
    Args:
        chunks: List of document chunks
        persist_directory: Directory to persist the vector store
        force_recreate: If True, recreate the vector store even if it exists
        
    Returns:
        Chroma vector store
    """
    # Use local HuggingFace embeddings (no API key needed)
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}  # Use 'cuda' if you have GPU
    )
    
    # Check if vector store already exists
    if os.path.exists(persist_directory) and not force_recreate:
        print(f"Loading existing vector store from {persist_directory}...")
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
        print("Vector store loaded successfully.")
    else:
        if force_recreate and os.path.exists(persist_directory):
            import shutil
            shutil.rmtree(persist_directory)
            print("Removed existing vector store.")
        
        if not chunks:
             print("No chunks to index. Returning empty initialized store if possible, or None.")
             # Create empty store if possible or handle gracefully
             # Chroma requires documents to initialize if not loading from disk
             if not os.path.exists(persist_directory):
                 return None 

        print("Creating new vector store...")
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        print(f"Vector store created and persisted to {persist_directory}.")
    
    return vector_store


def initialize_rag_system(force_recreate: bool = False):
    """
    Initialize the complete RAG system: load docs, split, and create vector store.
    
    Args:
        force_recreate: If True, recreate the vector store even if it exists
        
    Returns:
        Chroma vector store ready for retrieval
    """
    # Load Documents
    documents = load_documents()
    
    if not documents and force_recreate:
        print("No documents found to index.")
        return None

    # Split documents
    chunks = []
    if documents:
        chunks = split_documents(documents)
    
    # Create vector store
    vector_store = create_vector_store(chunks, force_recreate=force_recreate)
    
    return vector_store
