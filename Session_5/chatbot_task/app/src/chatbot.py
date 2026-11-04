

import chromadb
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from langchain_core.documents.base import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, Runnable
from langchain_chroma import Chroma
from chromadb.api import ClientAPI
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import requests
import re
from uuid import uuid5, NAMESPACE_URL
from typing import List
import logging
import os

# Hint: Use these variables in your tasks
OLLAMA_HOST_NAME = os.environ.get("OLLAMA_HOST_NAME", "localhost")
CHROMA_HOST_NAME = os.environ.get("CHROMA_HOST_NAME", "localhost")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-m3")
MODEL_NAME = os.environ.get("MODEL_NAME", "llama3.2:1b")
PDF_DOC_PATH = os.environ.get("PDF_DOC_PATH", "src/AI_Book.pdf")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "ai_model_book")
# Same chunking as in Session 3, so the collection built in the notebook and the one built here are identical
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "100"))
INDEX_BATCH_SIZE = 100

logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console logs
    ],
)

logger = logging.getLogger(__name__)

class CustomChatBot:
    """
    A class representing a chatbot that uses a ChromaDB client for document retrieval
    and the ChatOllama model for generating answers.

    This chatbot uses a retrieval-augmented generation (RAG) pipeline where it retrieves
    relevant information from a custom document database (ChromaDB) and then generates
    concise answers using a language model (ChatOllama).
    """

    def __init__(self, index_data: bool, pull_embedding_model: bool) -> None:
        """
        Initialize the CustomChatBot class by setting up the ChromaDB client for document retrieval
        and the ChatOllama language model for answer generation.
        """

        # Make sure the embedding model and the LLM are available in ollama (pulling is idempotent)
        if pull_embedding_model:
            for model in (EMBEDDING_MODEL, MODEL_NAME):
                self._pull_model(model)

        # Task: initialize the embedding model
        self.embedding_function = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=f"http://{OLLAMA_HOST_NAME}:11434")

        # Initialize the ChromaDB client
        self.client = self._initialize_chroma_client()
        
        # Get or create the document collection in ChromaDB
        self.vector_db = self._initialize_vector_db()

        # Process pdf, embedd data and index to ChromaDB.
        # INDEX_DATA=1 rebuilds the collection from scratch, an empty collection (fresh setup) is filled automatically.
        if index_data:
            logger.info("INDEX_DATA=1: rebuild the chroma collection now.")
            self.client.delete_collection(COLLECTION_NAME)
            self.vector_db = self._initialize_vector_db()
            self._index_data_to_vector_db()
        elif self.document_count() == 0:
            logger.info("Chroma collection is empty: index data to chroma db now.")
            self._index_data_to_vector_db()
        else:
            logger.info(f"Chroma collection already contains {self.document_count()} chunks, skip indexing.")

        # Task: Initialize the document retriever
        self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 3})

        # Task: Initialize the large language model (LLM) from Ollama
        self.llm = ChatOllama(model=MODEL_NAME, base_url=f"http://{OLLAMA_HOST_NAME}:11434")

        # Set up the retrieval-augmented generation (RAG) pipeline
        self.qa_rag_chain = self._initialize_qa_rag_chain()

    def _pull_model(self, model: str):
        """Download a model into the ollama container. Does nothing if the model is already there."""
        logger.info(f"Pull model {model} (this can take a while on the first start)")
        response = requests.post(f"http://{OLLAMA_HOST_NAME}:11434/api/pull", json={"name": model, "stream": False})
        response.raise_for_status()
        logger.info(f"{model}: {response.json()}")

    def document_count(self) -> int:
        """Number of chunks stored in the chroma collection."""
        return self.client.get_or_create_collection(COLLECTION_NAME).count()

    def _initialize_chroma_client(self) -> ClientAPI:
        """
        Initialize and return a ChromaDB HTTP client for document retrieval.

        Returns:
            chromadb.HttpClient: A client used to communicate with ChromaDB.
        """ 
        logger.info("Initialize chroma db client.")

        # Task: Initilaize chromadb http client
        return chromadb.HttpClient(
            host=CHROMA_HOST_NAME,
            port=8000,
            ssl=False,
            headers=None,
            settings=Settings(allow_reset=True, anonymized_telemetry=False),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )

    def _initialize_vector_db(self) -> Chroma:
        """
        Initialize and return a Chroma vector database using the HTTP client.

        Returns:
            Chroma: A vector database instance connected to the document collection in ChromaDB.
        """
        logger.info("Initialize chroma vector db.")

        # Task initialize langchain chromadb object with chromadb http client and embedding function
        return Chroma(
            client=self.client,
            collection_name=COLLECTION_NAME,
            embedding_function=self.embedding_function,
        )

    def _index_data_to_vector_db(self):

        pdf_doc = PDF_DOC_PATH
        logger.info(f"Building vector data base from {pdf_doc}")

        # Create pdf data loaders
        loader = PyPDFLoader(pdf_doc)

        # Load and split documents in chunks
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        pages_chunked = splitter.split_documents(loader.load())

        # Function to clean text by removing invalid unicode characters, including surrogate pairs
        def clean_text(text):
            # Remove surrogate pairs
            text = re.sub(r'[\ud800-\udfff]', '', text)
            # Optionally remove non-ASCII characters (depends on your use case)
            text = re.sub(r'[^\x00-\x7F]+', '', text)
            return text

        pages_chunked_cleaned = [
            Document(page_content=clean_text(doc.page_content), metadata=doc.metadata)
            for doc in pages_chunked
        ]

        # Remove empty chunks (e.g. pages that only contain images)
        pages_chunked_cleaned = [doc for doc in pages_chunked_cleaned if doc.page_content.strip()]

        # Deterministic ids: indexing the same book twice overwrites the chunks instead of adding duplicates
        doc_name = os.path.basename(pdf_doc)
        ids = [str(uuid5(NAMESPACE_URL, f"{doc_name}:{i}")) for i in range(len(pages_chunked_cleaned))]

        # Index the whole book in batches, so the progress is visible in the log
        for start in range(0, len(pages_chunked_cleaned), INDEX_BATCH_SIZE):
            end = start + INDEX_BATCH_SIZE
            self.vector_db.add_documents(documents=pages_chunked_cleaned[start:end], ids=ids[start:end])
            logger.info(f"Indexed {min(end, len(pages_chunked_cleaned))}/{len(pages_chunked_cleaned)} chunks")

        logger.info(f"Finished building vector database with {self.document_count()} chunks")

    def _initialize_qa_rag_chain(self) -> Runnable:
        """
        Set up the retrieval-augmented generation (RAG) pipeline for answering questions.
        
        The pipeline consists of:
        - Retrieving relevant documents from ChromaDB.
        - Formatting the retrieved documents for input into the language model (LLM).
        - Using the LLM to generate concise answers.
        
        Returns:
            dict: The RAG pipeline configuration.
        """
        logger.info("Initialize rag chain.")

        # Task: Define prompt
        prompt_template = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.

<context>
{context}
</context>

Answer the following question:

{question}"""

        # Task: Initialize prompt langchain prompt template
        rag_prompt = ChatPromptTemplate.from_template(prompt_template)

        # Task: Build the RAG pipeline using the retriever and LLM
        return (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | rag_prompt
            | self.llm
            | StrOutputParser()
        )

    def _format_docs(self, docs: List[Document]) -> str:
        """
        Helper function to format the retrieved documents into a single string.
        
        Args:
            docs (List[Document]): A list of documents retrieved by ChromaDB.

        Returns:
            str: A string containing the concatenated content of all retrieved documents.
        """
        return "\n\n".join(doc.page_content for doc in docs)
        
    async def astream(self, question: str):
        """
        Handle a user query asynchronously by running the question through the RAG pipeline and stream the answer.

        Args:
            question (str): The user's question as a string.

        Yields:
            str: The generated answer from the model, streamed chunk by chunk.
        """
        logger.info("Streaming RAG chain response.")
        try:
            async for event in self.qa_rag_chain.astream_events(question, version="v2"):
                # Task: Filter stream events to get the text chunk and yield it
                # Hint: filter for event["event"] == "on_chat_model_stream"
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"].content
                    yield chunk
        except Exception as e:
            logger.error(f"Error in stream_answer: {e}", exc_info=True)
            raise