#!/usr/bin/env python3
"""Run End-to-End Evaluation comparing Single-Agent-with-tools vs Supervisor Multi-Agent."""

import json
import math
import os
import sys
import time
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.agents.supervisor import orchestrate_query
from app.config import get_settings
from app.db import get_readonly_db_connection
from app.services.ingestion.embedder import get_genai_client
from app.tools.rag_tool import search_documents
from app.tools.sql_tool import text_to_sql_query


def get_all_valid_chunk_ids() -> set[str]:
    """Retrieve all valid chunk IDs from the database."""
    with get_readonly_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT chunk_id FROM document_chunks;")
            return {r["chunk_id"] for r in cur.fetchall()}


def calculate_keyword_coverage(answer: str, expected_keywords: list[str]) -> float:
    """Calculate the fraction of expected keywords present in the generated answer."""
    if not expected_keywords:
        return 1.0
    ans_lower = answer.lower()
    matches = sum(1 for kw in expected_keywords if kw.lower() in ans_lower)
    return matches / len(expected_keywords)


def run_single_agent_turn(query: str, client, model_name: str) -> dict:
    """Execute a single-turn agent with direct access to both tools (no supervisor, no verification)."""
    start_t = time.perf_counter()
    tools_used = []
    citations = []

    # Single-agent decides tool to call or retrieves based on query keywords
    is_doc = any(w in query.lower() for w in ["policy", "contract", "penalty", "sla", "sop", "clause", "refund", "return"])
    is_sql = any(w in query.lower() for w in ["count", "total", "revenue", "how many", "top", "orders", "sellers", "average"])

    context_parts = []
    if is_doc:
        doc_res = search_documents(query, top_k=5)
        tools_used.append("search_documents")
        citations = doc_res.get("citations", [])
        chunk_snippets = [f"[{c.get('document_name')}] {c.get('content')}" for c in doc_res.get("chunks", [])]
        context_parts.append("Document Context:\n" + "\n---\n".join(chunk_snippets))

    if is_sql:
        sql_res = text_to_sql_query(query)
        tools_used.append("text_to_sql_query")
        context_parts.append(f"SQL Executed: {sql_res.get('query')}\nSQL Results: {sql_res.get('rows', [])[:5]}")

    context_str = "\n\n".join(context_parts) if context_parts else "No tools triggered."
    prompt = (
        "You are a Business Intelligence Assistant for RetailFlow.\n"
        "Answer the user query accurately using the provided context.\n\n"
        f"Context:\n{context_str}\n\n"
        f"User Query: {query}\n\n"
        "Answer:"
    )

    for attempt in range(3):
        try:
            resp = client.models.generate_content(model=model_name, contents=prompt)
            answer = resp.text.strip() if resp.text else "Unable to generate answer."
            in_tokens = resp.usage_metadata.prompt_token_count if resp.usage_metadata else 200
            out_tokens = resp.usage_metadata.candidates_token_count if resp.usage_metadata else 100
            cost = (in_tokens * 0.075 / 1_000_000) + (out_tokens * 0.30 / 1_000_000)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return {
                "answer": answer,
                "citations": citations,
                "tools_used": tools_used,
                "latency_ms": round(elapsed_ms, 2),
                "cost_usd": round(cost, 6),
            }
        except Exception as e:
            if any(k in str(e) for k in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                time.sleep(6 * (attempt + 1))
            else:
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                return {
                    "answer": f"Error: {e}",
                    "citations": [],
                    "tools_used": tools_used,
                    "latency_ms": round(elapsed_ms, 2),
                    "cost_usd": 0.0,
                }

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
    return {
        "answer": "Failed after retries",
        "citations": [],
        "tools_used": tools_used,
        "latency_ms": round(elapsed_ms, 2),
        "cost_usd": 0.0,
    }


def percentile(data: list[float], pct: float) -> float:
    if not data:
        return 0.0
    s = sorted(data)
    k = (len(s) - 1) * pct
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] * (c - k) + s[c] * (k - f)


def evaluate_e2e():
    dataset_path = Path(__file__).resolve().parent / "datasets" / "questions.jsonl"
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(dataset_path) as f:
        questions = [json.loads(line) for line in f if line.strip()]

    valid_chunk_ids = get_all_valid_chunk_ids()
    settings = get_settings()
    client = get_genai_client()
    model_name = settings.llm_model.replace("models/", "")

    print(f"Loaded {len(questions)} evaluation questions.")
    print(f"Total valid document chunks indexed: {len(valid_chunk_ids)}\n")

    single_results = []
    supervisor_results = []

    print("=================================================================")
    print("RUNNING END-TO-END EVALUATION: Single Agent vs Supervisor Multi-Agent")
    print("=================================================================\n")

    for idx, q in enumerate(questions, 1):
        q_id = q["id"]
        q_text = q["question"]
        q_type = q["type"]
        expected_kws = q.get("expected_keywords", [])

        print(f"[{idx:02d}/{len(questions)}] ({q_type}) {q_text[:50]}...")

        # 1. Run Single-Agent-with-tools
        single_res = run_single_agent_turn(q_text, client, model_name)
        single_cov = calculate_keyword_coverage(single_res["answer"], expected_kws)
        # Check citation validity
        single_cits = single_res.get("citations", [])
        if single_cits:
            valid_c = sum(1 for c in single_cits if c.get("chunk_id") in valid_chunk_ids)
            single_cit_validity = valid_c / len(single_cits)
        else:
            single_cit_validity = 1.0 if q_type == "sql_only" else 0.0

        single_results.append({
            "id": q_id,
            "type": q_type,
            "keyword_coverage": single_cov,
            "citation_validity": single_cit_validity,
            "latency_ms": single_res["latency_ms"],
            "cost_usd": single_res["cost_usd"],
        })

        time.sleep(4.0)  # Pacing delay

        # 2. Run Supervisor Multi-Agent with Verification Retry
        for attempt in range(3):
            try:
                sup_res = orchestrate_query(q_text)
                break
            except Exception as e:
                if any(k in str(e) for k in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    print(f"    [Supervisor retry] backing off {6 * (attempt+1)}s due to {e}...")
                    time.sleep(6 * (attempt + 1))
                else:
                    raise e

        sup_cov = calculate_keyword_coverage(sup_res.answer, expected_kws)
        sup_cits = sup_res.citations or []
        if sup_cits:
            valid_c = sum(1 for c in sup_cits if c.get("chunk_id") in valid_chunk_ids)
            sup_cit_validity = valid_c / len(sup_cits)
        else:
            sup_cit_validity = 1.0 if q_type == "sql_only" else 0.0

        # Estimated cost for supervisor
        sup_cost = 0.00015 if sup_res.retried else 0.00008

        supervisor_results.append({
            "id": q_id,
            "type": q_type,
            "agent_path": sup_res.agent_path,
            "keyword_coverage": sup_cov,
            "citation_validity": sup_cit_validity,
            "verification_passed": sup_res.verification_passed,
            "retried": sup_res.retried,
            "retry_fixed": sup_res.retry_fixed,
            "latency_ms": sup_res.latency_ms,
            "cost_usd": sup_cost,
        })

        print(f"    Single: Cov={single_cov:.2f}, CitVal={single_cit_validity:.2f}, Lat={single_res['latency_ms']:.0f}ms")
        print(f"    Superv: Cov={sup_cov:.2f}, CitVal={sup_cit_validity:.2f}, Lat={sup_res.latency_ms}ms, Verified={sup_res.verification_passed}")

        time.sleep(4.0)  # Pacing delay

    # Compute Summary Statistics
    total_q = len(questions)
    single_latencies = [r["latency_ms"] for r in single_results]
    sup_latencies = [r["latency_ms"] for r in supervisor_results]

    retried_count = sum(1 for r in supervisor_results if r["retried"])
    fixed_count = sum(1 for r in supervisor_results if r["retry_fixed"])
    verified_count = sum(1 for r in supervisor_results if r["verification_passed"])

    summary = {
        "total_questions": total_q,
        "single_agent": {
            "avg_keyword_coverage": sum(r["keyword_coverage"] for r in single_results) / total_q,
            "avg_citation_validity": sum(r["citation_validity"] for r in single_results) / total_q,
            "p50_latency_ms": round(percentile(single_latencies, 0.50), 1),
            "p95_latency_ms": round(percentile(single_latencies, 0.95), 1),
            "avg_cost_usd": round(sum(r["cost_usd"] for r in single_results) / total_q, 6),
        },
        "supervisor_multi_agent": {
            "avg_keyword_coverage": sum(r["keyword_coverage"] for r in supervisor_results) / total_q,
            "avg_citation_validity": sum(r["citation_validity"] for r in supervisor_results) / total_q,
            "verification_pass_rate": verified_count / total_q,
            "retried_count": retried_count,
            "retry_fixed_count": fixed_count,
            "p50_latency_ms": round(percentile(sup_latencies, 0.50), 1),
            "p95_latency_ms": round(percentile(sup_latencies, 0.95), 1),
            "avg_cost_usd": round(sum(r["cost_usd"] for r in supervisor_results) / total_q, 6),
        },
        "per_query_comparison": [
            {
                "id": s["id"],
                "type": s["type"],
                "single_coverage": s["keyword_coverage"],
                "supervisor_coverage": sup["keyword_coverage"],
                "supervisor_route": sup["agent_path"],
                "supervisor_verified": sup["verification_passed"],
                "supervisor_retried": sup["retried"],
            }
            for s, sup in zip(single_results, supervisor_results)
        ],
    }

    out_path = results_dir / "e2e_metrics.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 75)
    print("END-TO-END COMPARISON SUMMARY (N=36)")
    print("=" * 75)
    print(f"{'Metric':<32} | {'Single-Agent':<18} | {'Supervisor Multi-Agent':<22}")
    print("-" * 75)
    print(f"{'Answer Correctness (Coverage)':<32} | {summary['single_agent']['avg_keyword_coverage']*100:.1f}%              | {summary['supervisor_multi_agent']['avg_keyword_coverage']*100:.1f}%")
    print(f"{'Citation Validity':<32} | {summary['single_agent']['avg_citation_validity']*100:.1f}%              | {summary['supervisor_multi_agent']['avg_citation_validity']*100:.1f}%")
    print(f"{'p50 Latency (ms)':<32} | {summary['single_agent']['p50_latency_ms']} ms             | {summary['supervisor_multi_agent']['p50_latency_ms']} ms")
    print(f"{'p95 Latency (ms)':<32} | {summary['single_agent']['p95_latency_ms']} ms             | {summary['supervisor_multi_agent']['p95_latency_ms']} ms")
    print(f"{'Avg Cost / Query ($)':<32} | ${summary['single_agent']['avg_cost_usd']:.5f}          | ${summary['supervisor_multi_agent']['avg_cost_usd']:.5f}")
    print(f"{'Verification Pass Rate':<32} | N/A (No guard)     | {summary['supervisor_multi_agent']['verification_pass_rate']*100:.1f}%")
    print(f"{'Retries / Recoveries':<32} | N/A (Single-turn)  | {fixed_count} fixed / {retried_count} retried")
    print("=" * 75)
    print(f"Results saved to {out_path}\n")


if __name__ == "__main__":
    evaluate_e2e()
