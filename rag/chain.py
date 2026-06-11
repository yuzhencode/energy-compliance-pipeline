"""
rag/chain.py
============
Builds the LangChain RAG chain using:
  - ChromaDB as vector store
  - sentence-transformers/all-MiniLM-L6-v2 for embeddings
  - Ollama llama3.2:3b as LLM
"""

from pathlib import Path

from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM

CHROMA_DIR = Path(__file__).parent / "chroma_db"

PROMPT_TEMPLATE = """You are an Ofgem compliance assistant for UK energy suppliers.
Answer the question using only the context provided below.
If the answer is not in the context, say "I don't have enough information in the loaded Ofgem documents to answer this."
Always cite the source document name when you use information from it.

Context:
{context}

Question: {question}

Answer:"""


def build_chain() -> RetrievalQA:
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="ofgem_docs",
    )
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )
    llm = OllamaLLM(
        model="llama3.2:3b",
        temperature=0.1,
    )
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"],
    )
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )
    return chain
