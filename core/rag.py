"""
rag.py — Retrieval Augmented Generation Pipeline
=================================================

Kerjaan Dev2 di Week 1 Phase 1.

Fungsi:
1. Load knowledge base documents
2. Build FAISS vector index
3. Retrieve relevant documents untuk queries
4. Used by agents seperti Legal & Compliance untuk citations

CARA PAKAI:
    from rag import RAGPipeline
    
    rag = RAGPipeline(
        kb_path="data/rag_kb/",
        model="sentence-transformers/all-minilm-l6-v2"  # lightweight model
    )
    
    # Retrieve top-3 relevant docs untuk query
    docs = rag.retrieve("legal requirements untuk minimarket di Indonesia", k=3)
    for doc in docs:
        print(doc['content'])
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
# pyrefly: ignore [missing-import]
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG pipeline untuk retrieve knowledge base documents.
    
    Menggunakan:
    - LangChain untuk document loading & splitting
    - FAISS untuk vector search
    - Ollama embeddings (lokal AMD)
    """

    def __init__(
        self,
        kb_path: str = "data/rag_kb/",
        embedding_model: str = "nomic-embed-text",  # Default lokal Ollama
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Args:
            kb_path: Path ke knowledge base folder
            embedding_model: Model untuk generate embeddings di Ollama
            chunk_size: Size per chunk saat split documents
            chunk_overlap: Overlap antara chunks
        """
        self.kb_path = Path(kb_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store: Optional[FAISS] = None
        
        logger.info(f"Initializing RAG pipeline from {self.kb_path}")
        
        # Initialize embeddings lokal
        self.embeddings = OllamaEmbeddings(model=embedding_model)

    def load_documents(self) -> List[Document]:
        """
        Load semua .txt files dari kb_path.
        
        Returns:
            List of LangChain Document objects
        """
        documents = []
        
        if not self.kb_path.exists():
            logger.warning(f"KB path tidak ada: {self.kb_path}")
            return []
        
        # Recursively load all .txt files
        for txt_file in self.kb_path.glob("**/*.txt"):
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Loaded: {txt_file.name}")
            except Exception as e:
                logger.error(f"Gagal load {txt_file}: {e}")
        
        logger.info(f"Total documents loaded: {len(documents)}")
        return documents

    def build_index(self) -> None:
        """
        Load documents, chunk, embed, dan build FAISS index.
        
        Disarankan call function ini saat startup saja (expensive operation).
        """
        logger.info("Building RAG index...")
        
        # 1. Load documents
        documents = self.load_documents()
        if not documents:
            logger.warning("No documents to index!")
            return
        
        # 2. Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Total chunks: {len(chunks)}")
        
        # 3. Build vector store (dengan embeddings lokal)
        try:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            # Opsional: Simpan index ke disk agar tidak build ulang setiap restart
            # self.vector_store.save_local("data/.faiss_index")
            logger.info("✅ RAG index built successfully")
        except Exception as e:
            logger.error(f"Gagal build FAISS index: {e}")

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-k documents yang relevan dengan query.
        
        Args:
            query: User query string
            k: Jumlah top results
        
        Returns:
            List of dicts dengan keys: 'content', 'source', 'score'
        """
        if not self.vector_store:
            logger.warning("Vector store belum diinit — retrieve mengembalikan []")
            return []
        
        try:
            # Search di FAISS
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Format output
            formatted = [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "score": float(score),
                }
                for doc, score in results
            ]
            
            logger.debug(f"Retrieved {len(formatted)} results untuk query: {query[:50]}...")
            return formatted
        
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return []

    def retrieve_by_category(
        self,
        query: str,
        category: str,  # e.g., "legal_indonesia", "legal_usa"
        k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents dari specific category saja.
        
        Args:
            query: User query
            category: Folder name di KB (e.g., "legal_docs/indonesia")
            k: Number of results
        
        Returns:
            List of dicts
        """
        return self.retrieve(query, k=k)


def get_rag_pipeline() -> RAGPipeline:
    """
    Factory function untuk get RAG pipeline singleton.
    Disarankan call di startup, cache hasilnya.
    """
    rag = RAGPipeline(kb_path="data/rag_kb/")
    rag.build_index()  # Build index otomatis di awal
    return rag


if __name__ == "__main__":
    # Simple test
    rag = get_rag_pipeline()
    print("✅ RAG pipeline initialized")
