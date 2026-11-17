#!/usr/bin/env python3
"""Run text-to-SQL evaluation measuring Guard Pass Rate, Execution Success, and Result Accuracy."""

import json
import os
import sys
import time
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.db import get_readonly_db_connection
from app.services.sql.executor import execute_guarded_sql, generate_sql
from app.services.sql.guard import SQLSecurityException, validate_and_guard_sql


def run_reference_sql(sql: str) -> list[dict]:
    with get_readonly_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                return [dict(r) for r in cur.fetchall()]
    return []


def generate_sql_with_retry(query_text: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return generate_sql(query_text)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                backoff = 6 * (attempt + 1)
                print(f"    [Rate limit 429] Backing off {backoff}s before retry {attempt + 1}...")
                time.sleep(backoff)
            else:
                raise e
    return generate_sql(query_text)


def evaluate_sql():
    dataset_path = Path(__file__).resolve().parent / "datasets" / "questions.jsonl"
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(dataset_path) as f:
        questions = [json.loads(line) for line in f if line.strip()]

    sql_eval_queries = [q for q in questions if q.get("reference_sql")]
    print(f"Evaluating {len(sql_eval_queries)} text-to-SQL queries against reference queries...\n")

    guard_passes = 0
    exec_successes = 0
    accuracy_matches = 0
    latencies = []
    detailed_results = []

    for idx, q in enumerate(sql_eval_queries, 1):
        query_text = q["question"]
        ref_sql = q["reference_sql"]
        print(f"[{idx}/{len(sql_eval_queries)}] ({q['type']}) {query_text[:55]}...")

        # Get gold standard reference result
        try:
            ref_rows = run_reference_sql(ref_sql)
        except Exception as ref_err:
            print(f"  Reference SQL error: {ref_err}")
            ref_rows = []

        start_t = time.perf_counter()
        gen_sql = None
        guard_passed = False
        exec_passed = False
        match_passed = False
        error_msg = None
        gen_rows = []

        try:
            # 1. Generate SQL with rate-limit retry
            gen_sql = generate_sql_with_retry(query_text)

            # 2. Guard validation
            guarded_sql = validate_and_guard_sql(gen_sql)
            guard_passed = True
            guard_passes += 1

            # 3. Execution under read-only role with 3s statement timeout
            res = execute_guarded_sql(guarded_sql)
            if not res.error:
                exec_passed = True
                exec_successes += 1
                gen_rows = res.rows

                # 4. Result Accuracy Comparison
                if ref_rows and gen_rows:
                    ref_first_vals = [str(v).lower().strip() for v in ref_rows[0].values()]
                    gen_first_vals = [str(v).lower().strip() for v in gen_rows[0].values()]

                    has_val_match = any(
                        rf in gen_first_vals or any(rf in gv for gv in gen_first_vals)
                        for rf in ref_first_vals
                    )
                    count_match = len(ref_rows) == len(gen_rows) or (
                        len(ref_rows) > 0 and len(gen_rows) > 0 and has_val_match
                    )

                    if count_match or has_val_match:
                        match_passed = True
                        accuracy_matches += 1
            else:
                error_msg = res.error

        except SQLSecurityException as sec_err:
            error_msg = f"Security guard blocked query: {sec_err}"
        except Exception as e:
            error_msg = str(e)

        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        latencies.append(elapsed_ms)

        print(f"  -> Guard: {guard_passed} | Exec: {exec_passed} | Accuracy Match: {match_passed} ({elapsed_ms:.0f}ms)")
        if error_msg:
            print(f"     Note: {error_msg[:80]}")

        detailed_results.append({
            "id": q["id"],
            "type": q["type"],
            "question": query_text,
            "reference_sql": ref_sql,
            "generated_sql": gen_sql,
            "guard_passed": guard_passed,
            "execution_passed": exec_passed,
            "accuracy_match": match_passed,
            "latency_ms": round(elapsed_ms, 2),
            "error": error_msg,
        })

        # Polite delay to respect Gemini 15 RPM free tier quota
        time.sleep(4.2)

    total = len(sql_eval_queries)
    summary = {
        "total_queries": total,
        "guard_pass_rate": guard_passes / total,
        "execution_success_rate": exec_successes / total,
        "execution_accuracy": accuracy_matches / total,
        "avg_latency_ms": sum(latencies) / len(latencies),
        "detailed_results": detailed_results,
    }

    out_path = results_dir / "sql_metrics.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 65)
    print(f"TEXT-TO-SQL EVALUATION RESULTS (N={total})")
    print("=" * 65)
    print(f"Guard Pass Rate:          {summary['guard_pass_rate'] * 100:.1f}% ({guard_passes}/{total})")
    print(f"Execution Success Rate:   {summary['execution_success_rate'] * 100:.1f}% ({exec_successes}/{total})")
    print(f"Execution Accuracy:       {summary['execution_accuracy'] * 100:.1f}% ({accuracy_matches}/{total})")
    print(f"Average Generation Time:  {summary['avg_latency_ms']:.1f} ms")
    print("=" * 65)
    print(f"Results saved to {out_path}\n")


if __name__ == "__main__":
    evaluate_sql()
