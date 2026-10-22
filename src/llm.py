"""Selector de proveedor de LLM y de embeddings (100% gratuitos)."""
import hashlib
import math
import os
import re

from langchain_core.embeddings import Embeddings

from . import config


class LLMUnavailable(RuntimeError):
    pass


def get_llm():
    """Devuelve un chat model o None si el proveedor es 'rules' (sin LLM)."""
    provider = config.llm_provider()
    if provider == "rules":
        return None
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise LLMUnavailable("GROQ_API_KEY no está definida en .env")
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=0,
            timeout=30,
            max_retries=1,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
            temperature=0,
            client_kwargs={"timeout": 60},
        )
    raise LLMUnavailable(f"LLM_PROVIDER desconocido: {provider}")


class HashingEmbeddings(Embeddings):
    """Embeddings deterministas por hashing de palabras (bolsa de palabras).
    Solo para pruebas offline: no captura sinónimos como un modelo real."""

    def __init__(self, dim: int = 384):
        self.dim = dim

    @staticmethod
    def _tokens(text: str):
        return [t for t in re.findall(r"[a-záéíóúñ0-9]+", text.lower()) if len(t) > 2]

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for tok in self._tokens(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)


def get_embeddings() -> Embeddings:
    if config.embeddings_provider() == "fake":
        return HashingEmbeddings()
    from langchain_ollama import OllamaEmbeddings

    return OllamaEmbeddings(model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"))
