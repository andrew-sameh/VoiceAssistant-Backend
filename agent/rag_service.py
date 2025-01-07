import os
import logging
from pinecone.grpc import PineconeGRPC as Pinecone
from openai import OpenAI

logger = logging.getLogger("RAG")

class RAGService:
    def __init__(self):
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.top_k = 4
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.pc.Index(self.index_name)

    def get_embeddings(self, query: str):
        res = self.openai_client.embeddings.create(
            input=query, model="text-embedding-3-small"
        )
        return res.data[0].embedding

    def serialize_results(self, results):
        if not results or "matches" not in results:
            return "No matches found in the results."

        formatted_results = []

        for match in results["matches"]:
            page = int(match["metadata"].get("page", "Unknown"))
            text = match["metadata"].get("text", "").strip()
            formatted_results.append(f"Page {page}: {text}\n")

        return "\n---\n".join(formatted_results)

    def retrieve_docs(self, query: str, namespace: str) -> str:
        vector = self.get_embeddings(query)
        results = self.index.query(
            vector=vector,
            top_k=self.top_k,
            namespace=namespace,
            include_values=False,
            include_metadata=True,
        )
        serialized = self.serialize_results(results)
        return serialized
