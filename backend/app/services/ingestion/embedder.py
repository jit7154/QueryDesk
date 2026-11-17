import time

from google import genai
from google.genai import errors, types

from app.config import get_settings

_client: genai.Client | None = None


def get_genai_client() -> genai.Client:
    """Return cached Gemini API client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def embed_text(text: str) -> list[float]:
    """Generate a 768-dimensional embedding vector for a single query or text."""
    settings = get_settings()
    client = get_genai_client()
    model_name = settings.embedding_model.replace("models/", "")
    for attempt in range(4):
        try:
            response = client.models.embed_content(
                model=model_name,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dim),
            )
            return response.embeddings[0].values
        except errors.ClientError as err:
            if "429" in str(err) and attempt < 3:
                time.sleep(10 * (attempt + 1))
            else:
                raise
    return []


def embed_batch(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """Generate 768-dimensional embeddings for a batch of text chunks with rate-limit backoff."""
    if not texts:
        return []
    settings = get_settings()
    client = get_genai_client()
    model_name = settings.embedding_model.replace("models/", "")
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        success = False
        for attempt in range(4):
            try:
                response = client.models.embed_content(
                    model=model_name,
                    contents=batch,
                    config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dim),
                )
                for emb in response.embeddings:
                    all_embeddings.append(emb.values)
                success = True
                time.sleep(1.0)
                break
            except errors.ClientError as err:
                if "429" in str(err) and attempt < 3:
                    time.sleep(12 * (attempt + 1))
                else:
                    raise
        if not success:
            raise RuntimeError(f"Failed to embed batch starting at index {i}")

    return all_embeddings
