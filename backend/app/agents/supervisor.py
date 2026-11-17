import time
from dataclasses import dataclass
from typing import Any

from google.adk import Agent

from app.agents.data_analyst_agent import get_data_analyst_agent, run_data_analyst_agent
from app.agents.knowledge_agent import get_knowledge_agent, run_knowledge_agent
from app.config import get_settings
from app.services.ingestion.embedder import get_genai_client
from app.services.observability.usage_logger import log_query_execution
from app.services.retrieval.hybrid import chunks_to_citations, hybrid_retrieve
from app.services.sql.executor import run_text_to_sql
from app.services.verification.checks import verify_response

SUPERVISOR_INSTRUCTION = (
    "You are the Lead Supervisor Agent for QueryDesk. Your role is to understand user business "
    "inquiries for RetailFlow, determine whether answering requires unstructured document "
    "search (Knowledge Agent), relational database queries (Data Analyst Agent), or both (Hybrid), "
    "and coordinate sub-agents to deliver accurate, citation-backed answers."
)


@dataclass
class SupervisorResult:
    answer: str
    agent_path: str
    citations: list[dict[str, Any]]
    sql_query: str | None
    sql_rows: list[dict[str, Any]]
    verification_passed: bool
    retried: bool
    retry_fixed: bool
    latency_ms: int
    execution_steps: list[str]


def generate_content_with_retry(
    client: Any, model: str, contents: str, max_retries: int = 3
) -> Any:
    """Generate content with exponential backoff on 429 quota and 503 transient demand spikes."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=contents)
        except Exception as exc:
            err_str = str(exc)
            if any(k in err_str for k in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                backoff = 4 * (attempt + 1)
                time.sleep(backoff)
            else:
                raise exc
    return client.models.generate_content(model=model, contents=contents)


def get_supervisor_agent() -> Agent:
    """Instantiate Google ADK Supervisor Agent orchestrating knowledge and data analyst agents."""
    settings = get_settings()
    model_name = settings.llm_model.replace("models/", "")
    return Agent(
        name="supervisor",
        model=model_name,
        instruction=SUPERVISOR_INSTRUCTION,
        sub_agents=[get_knowledge_agent(), get_data_analyst_agent()],
    )


def classify_intent(query: str) -> str:
    """Classify user question intent into document_only, sql_only, or hybrid."""
    settings = get_settings()
    client = get_genai_client()
    model_name = settings.llm_model.replace("models/", "")

    prompt = (
        "Classify the following e-commerce business query into exactly one category:\n"
        "- document_only: Questions about policies, warranty, SLAs, clauses, refund steps, SOPs.\n"
        "- sql_only: Questions asking for counts, revenues, sales volumes, customer numbers.\n"
        "- hybrid: Questions requiring both company documents (e.g. penalty clauses) AND database "
        "metrics (e.g. calculating penalty owed by a specific seller for late orders).\n\n"
        f"Query: {query}\n"
        "Return ONLY one of: document_only, sql_only, hybrid."
    )

    try:
        resp = generate_content_with_retry(
            client=client,
            model=model_name,
            contents=prompt,
        )
        cat = resp.text.strip().lower() if resp.text else "hybrid"
        if "sql" in cat and "hybrid" not in cat:
            return "sql_only"
        elif "document" in cat:
            return "document_only"
        return "hybrid"
    except Exception:
        # Fall back to hybrid when intent is ambiguous
        return "hybrid"


HybridResult = tuple[str, list[dict[str, Any]], str | None, list[dict[str, Any]], list[str]]


def run_hybrid_orchestration(query: str) -> HybridResult:
    """Execute joint multi-agent retrieval and SQL calculation workflow."""
    steps = ["Decomposing hybrid query", "Searching contractual and policy documents"]
    chunks = hybrid_retrieve(query, top_k=5)
    citations = [c.model_dump() for c in chunks_to_citations(chunks)]

    doc_blocks = [
        f"[{c.document_name}, {c.section_title}, p.{c.page_number}]: {c.content}"
        for c in chunks
    ]
    doc_context = "\n\n".join(doc_blocks)

    steps.append("Translating query to database metrics based on document context")
    settings = get_settings()
    client = get_genai_client()
    model_name = settings.llm_model.replace("models/", "")

    sql_prompt = (
        "Based on the following document context and user question, write a single PostgreSQL "
        "SELECT query to pull the necessary data from orders, order_items, sellers, "
        "customers, or products.\n\n"
        f"Document Context:\n{doc_context}\n\n"
        f"User Question:\n{query}\n\n"
        "Return ONLY plain SQL (no markdown fences, no explanation):"
    )

    sql_resp = generate_content_with_retry(client, model=model_name, contents=sql_prompt)
    raw_sql = sql_resp.text.strip() if sql_resp.text else ""
    if raw_sql.startswith("```"):
        filtered_lines = [line for line in raw_sql.splitlines() if not line.startswith("```")]
        raw_sql = "\n".join(filtered_lines).strip()

    steps.append("Executing guarded SQL query under read-only database role")
    from app.services.sql.executor import execute_guarded_sql
    from app.services.sql.guard import validate_and_guard_sql

    try:
        guarded_sql = validate_and_guard_sql(raw_sql)
        sql_res = execute_guarded_sql(guarded_sql)
    except Exception:
        sql_res = run_text_to_sql(query)

    steps.append("Synthesizing unified answer with legal citations and database findings")
    synth_prompt = (
        "You are QueryDesk. Synthesize a complete, professional business answer to the question.\n"
        "Requirements:\n"
        "1. Cite exact documents and sections from context (e.g. [Doc.pdf, Sec X, p.Y]).\n"
        "2. State the exact numeric findings from the SQL results accurately.\n"
        "3. If computing penalties or deductions, show the calculation step from the clause.\n\n"
        f"User Question: {query}\n\n"
        f"Document Context:\n{doc_context}\n\n"
        f"SQL Query: {sql_res.query}\n"
        f"SQL Result Data: {sql_res.rows[:10]}\n\n"
        "Answer:"
    )

    synth_resp = generate_content_with_retry(client, model=model_name, contents=synth_prompt)
    answer = synth_resp.text.strip() if synth_resp.text else "Unable to synthesize answer."

    return answer, citations, sql_res.query, sql_res.rows, steps


def orchestrate_query(query: str) -> SupervisorResult:
    """Supervise query routing, execute sub-agents, verify consistency, and audit log."""
    start_time = time.perf_counter()
    steps = ["Classifying intent"]
    agent_path = classify_intent(query)
    steps.append(f"Routing to path: {agent_path}")

    sql_query: str | None = None
    sql_rows: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []
    valid_cids: set[str] = set()

    if agent_path == "document_only":
        steps.append("Knowledge Agent retrieving documents")
        res = run_knowledge_agent(query)
        answer = res["answer"]
        citations = res["citations"]
        valid_cids = set(res["chunks_used"])
    elif agent_path == "sql_only":
        steps.append("Data Analyst Agent generating and executing SQL")
        res = run_data_analyst_agent(query)
        answer = res["answer"]
        sql_query = res.get("sql_query")
        sql_rows = res.get("sql_rows", [])
    else:
        answer, citations, sql_query, sql_rows, hybrid_steps = run_hybrid_orchestration(query)
        steps.extend(hybrid_steps)
        valid_cids = {c.get("chunk_id", "") for c in citations}

    # Deterministic verification step
    steps.append("Verifying cited chunks and numerical consistency")
    cited_cids = [c["chunk_id"] for c in citations if "chunk_id" in c]
    verif_passed, verif_msg = verify_response(
        answer=answer,
        cited_chunk_ids=cited_cids,
        valid_chunk_ids=valid_cids,
        sql_rows=sql_rows if sql_rows else None,
    )

    retried = False
    retry_fixed = False

    # Retry once with structured feedback if verification failed
    if not verif_passed:
        retried = True
        steps.append(f"Verification issue detected ({verif_msg}). Executing feedback retry.")
        settings = get_settings()
        client = get_genai_client()
        model_name = settings.llm_model.replace("models/", "")

        retry_prompt = (
            "Your previous answer had a verification issue: "
            f"{verif_msg}\n\n"
            "Please revise the answer to ensure:\n"
            "1. All numerical quantities strictly match the provided SQL results.\n"
            "2. All citations reference only the provided document sources.\n\n"
            f"Original Question: {query}\n"
            f"Original Draft: {answer}\n"
            f"SQL Rows: {sql_rows[:10]}\n\n"
            "Corrected Answer:"
        )

        try:
            retry_resp = generate_content_with_retry(
                client, model=model_name, contents=retry_prompt
            )
            if retry_resp.text:
                new_answer = retry_resp.text.strip()
                new_passed, _ = verify_response(
                    answer=new_answer,
                    cited_chunk_ids=cited_cids,
                    valid_chunk_ids=valid_cids,
                    sql_rows=sql_rows if sql_rows else None,
                )
                if new_passed:
                    answer = new_answer
                    verif_passed = True
                    retry_fixed = True
                    steps.append("Verification passed after retry correction")
        except Exception:
            pass

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    # Persist usage logging for analytics
    input_tokens = len(query.split()) * 4 + 200
    output_tokens = len(answer.split()) * 4
    log_query_execution(
        query_text=query,
        agent_path=agent_path,
        latency_ms=elapsed_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        sql_query=sql_query,
        verification_passed=verif_passed,
        retried=retried,
        retry_fixed=retry_fixed,
        tool_calls=[{"agent": agent_path, "sql": sql_query}],
        citations=citations,
    )

    return SupervisorResult(
        answer=answer,
        agent_path=agent_path,
        citations=citations,
        sql_query=sql_query,
        sql_rows=sql_rows,
        verification_passed=verif_passed,
        retried=retried,
        retry_fixed=retry_fixed,
        latency_ms=elapsed_ms,
        execution_steps=steps,
    )
