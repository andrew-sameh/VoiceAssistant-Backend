import os
import logging
import shutil
from fastapi import HTTPException, UploadFile
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader,
)
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from typing import List
from sqlalchemy.orm import Session

logger = logging.getLogger("api")
class DocumentProcessor:
    def __init__(self):
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.top_k = 4
        self.llm = ChatOpenAI(api_key=self.openai_api_key, model="gpt-4o-mini")
        self.embeddings = OpenAIEmbeddings(
            api_key=self.openai_api_key, model="text-embedding-3-small"
        )
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            pinecone_api_key=self.pinecone_api_key,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, add_start_index=True
        )

    def load_and_split_document(self, file_path: str) -> List[Document]:
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif file_path.endswith(".html"):
            loader = UnstructuredHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

        documents = loader.load()
        return self.text_splitter.split_documents(documents)

    def serialize_docs(self, docs: List[Document]) -> str:
        return "\n\n".join(
            (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}") for doc in docs
        )

    async def retrieve_docs(self, query: str, namespace: str) -> str:
        results = await self.vectorstore.asimilarity_search(
            query, k=self.top_k, namespace=namespace
        )
        serialized = self.serialize_docs(results)
        return serialized

    def process_file_upload(
        self, file: UploadFile, namespace: str
    ):

        temp_file_path = f"temp_{file.filename}"

        try:
            # Save the uploaded file to a temporary file
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.info(f"Saved file to {temp_file_path}")
            # Load and split the document
            documents = self.load_and_split_document(temp_file_path)
            logger.info(f"Loaded and split {len(documents)} documents")
            ids = self.vectorstore.add_documents(documents, namespace=namespace)
            logger.info(f"Indexed {len(ids)} documents and added to pinecone with the namespace {namespace}")
            if ids:
                overview = self.document_overview(documents)
                return overview
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to index {file.filename}, {str(e)}"
            )
        finally:
            if os.path.exists(temp_file_path):
                logger.info(f"Removing temporary file {temp_file_path}")
                os.remove(temp_file_path)

    def document_overview(self, documents: List[Document]) -> str:
        template = f"""You are an expert summarizer and your task is to provide a concise and clear overview of the content of a document. Analyze the first few sections of the provided text to determine its main themes, purpose, and structure. Focus on identifying the document's key topics, objectives, and any overarching message or argument.

        Output format:

        Purpose: [Brief explanation of why the document was created]
        Key Topics: [List of main topics covered in the introduction/first sections]
        Structure Overview: [Summary of how the document is organized]
        Audience: [Intended audience if discernible]
        
        Text to analyze:
        {{context}}

        Document overview:"""
        serialized_docs = self.serialize_docs(documents[:4])

        prompt = PromptTemplate.from_template(template)
        formatted_prompt = prompt.format(context=serialized_docs)
        logger.info(f"Generated prompt for document overview")
        res = self.llm.invoke(formatted_prompt)
        print(res.content)
        return res.content
