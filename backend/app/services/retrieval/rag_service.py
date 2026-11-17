import time

from app.config import get_settings
from app.schemas.rag import RAGQueryResponse
from app.services.ingestion.embedder import get_genai_client
from app.services.retrieval.hybrid import chunks_to_citations, hybrid_retrieve


def answer_document_query(query: str, top_k: int = 5) -> RAGQueryResponse:
    """Retrieve relevant document chunks via hybrid RRF and generate cited answer."""
    chunks = hybrid_retrieve(query, top_k=top_k)
    citations = chunks_to_citations(chunks)

    if not chunks:
        return RAGQueryResponse(
            query=query,
            answer="No relevant documents were found in the knowledge base to answer this query.",
            citations=[],
            retrieval_method="hybrid_rrf",
        )

    context_blocks = []
    for c in chunks:
        header = (
            f"Source: {c.document_name} | {c.section_title} | "
            f"Page {c.page_number} (Chunk ID: {c.chunk_id})"
        )
        context_blocks.append(f"{header}\n{c.content}")

    context_str = "\n\n---\n\n".join(context_blocks)

    system_instruction = (
        "You are QueryDesk, an enterprise AI assistant for RetailFlow. "
        "Answer the user query accurately and concisely using ONLY the provided document context. "
        "Always cite relevant sources with their document name, section number, and page number "
        "(e.g., [Supplier_Contract_Apex_6560211a19b4.pdf, Section 7.2, p.2]). "
        "Do not invent facts or extrapolate beyond the provided text. "
        "If information is missing, state it plainly."
    )

    prompt = (
        f"{system_instruction}\n\n"
        f"Context:\n{context_str}\n\n"
        f"User Question:\n{query}\n\n"
        f"Answer:"
    )

    settings = get_settings()
    client = get_genai_client()
    model_name = settings.llm_model.replace("models/", "")

    answer_text = "Unable to generate an answer."
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            answer_text = (
                response.text.strip() if response.text else "Unable to generate an answer."
            )
            break
        except Exception as exc:
            err_str = str(exc)
            if any(k in err_str for k in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                time.sleep(4 * (attempt + 1))
            else:
                answer_text = f"An error occurred while generating the answer: {exc}"
                break

    return RAGQueryResponse(
        query=query,
        answer=answer_text,
        citations=citations,
        retrieval_method="hybrid_rrf",
    )
