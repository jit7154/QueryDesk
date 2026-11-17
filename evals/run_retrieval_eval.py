#!/usr/bin/env python3
"""Run retrieval evaluation comparing BM25, Dense Vector (pgvector HNSW), and Hybrid RRF."""

import json
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.ingestion.embedder import embed_text
from app.services.retrieval.bm25_search import search_bm25
from app.services.retrieval.hybrid import hybrid_retrieve
from app.services.retrieval.vector_search import search_vector


def evaluate_retrieval():
    dataset_path = Path(__file__).resolve().parent / "datasets" / "questions.jsonl"
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(dataset_path) as f:
        questions = [json.loads(line) for line in f if line.strip()]

    # Filter for questions that target documents
    doc_eval_queries = [q for q in questions if q.get("target_documents")]
    print(f"Evaluating {len(doc_eval_queries)} queries with target documents...\n")

    bm25_recalls, bm25_mrrs = [], []
    vec_recalls, vec_mrrs = [], []
    hybrid_recalls, hybrid_mrrs = [], []

    detailed_results = []

    for idx, q in enumerate(doc_eval_queries, 1):
        query_text = q["question"]
        target_docs = set(q["target_documents"])
        print(f"[{idx}/{len(doc_eval_queries)}] Query: {query_text[:60]}...")

        # 1. BM25 Search
        bm25_results = search_bm25(query_text, top_k=5)
        bm25_hit_rank = None
        for rank, chunk in enumerate(bm25_results, 1):
            if chunk.document_name in target_docs:
                bm25_hit_rank = rank
                break
        bm25_rec = 1.0 if bm25_hit_rank is not None else 0.0
        bm25_mrr = (1.0 / bm25_hit_rank) if bm25_hit_rank is not None else 0.0
        bm25_recalls.append(bm25_rec)
        bm25_mrrs.append(bm25_mrr)

        # 2. Vector Search (pgvector HNSW)
        query_emb = embed_text(query_text)
        vec_results = search_vector(query_emb, top_k=5)
        vec_hit_rank = None
        for rank, chunk in enumerate(vec_results, 1):
            if chunk.document_name in target_docs:
                vec_hit_rank = rank
                break
        vec_rec = 1.0 if vec_hit_rank is not None else 0.0
        vec_mrr = (1.0 / vec_hit_rank) if vec_hit_rank is not None else 0.0
        vec_recalls.append(vec_rec)
        vec_mrrs.append(vec_mrr)

        # 3. Hybrid RRF Search
        hybrid_results = hybrid_retrieve(query_text, top_k=5)
        hybrid_hit_rank = None
        for rank, chunk in enumerate(hybrid_results, 1):
            if chunk.document_name in target_docs:
                hybrid_hit_rank = rank
                break
        hybrid_rec = 1.0 if hybrid_hit_rank is not None else 0.0
        hybrid_mrr = (1.0 / hybrid_hit_rank) if hybrid_hit_rank is not None else 0.0
        hybrid_recalls.append(hybrid_rec)
        hybrid_mrrs.append(hybrid_mrr)

        detailed_results.append({
            "id": q["id"],
            "question": query_text,
            "target_documents": list(target_docs),
            "bm25": {"hit_rank": bm25_hit_rank, "recall@5": bm25_rec, "mrr": bm25_mrr},
            "vector": {"hit_rank": vec_hit_rank, "recall@5": vec_rec, "mrr": vec_mrr},
            "hybrid": {"hit_rank": hybrid_hit_rank, "recall@5": hybrid_rec, "mrr": hybrid_mrr},
        })

    summary = {
        "total_queries": len(doc_eval_queries),
        "bm25": {
            "recall@5": sum(bm25_recalls) / len(bm25_recalls),
            "mrr": sum(bm25_mrrs) / len(bm25_mrrs),
        },
        "vector": {
            "recall@5": sum(vec_recalls) / len(vec_recalls),
            "mrr": sum(vec_mrrs) / len(vec_mrrs),
        },
        "hybrid_rrf": {
            "recall@5": sum(hybrid_recalls) / len(hybrid_recalls),
            "mrr": sum(hybrid_mrrs) / len(hybrid_mrrs),
        },
        "detailed_results": detailed_results,
    }

    # Save to JSON
    out_path = results_dir / "retrieval_metrics.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary table
    print("\n" + "=" * 65)
    print("RETRIEVAL EVALUATION RESULTS (N=24)")
    print("=" * 65)
    print(f"{'Method':<25} | {'Recall@5':<15} | {'MRR':<15}")
    print("-" * 65)
    print(f"{'BM25 (Sparse)':<25} | {summary['bm25']['recall@5']:.4f}          | {summary['bm25']['mrr']:.4f}")
    print(f"{'Vector (pgvector HNSW)':<25} | {summary['vector']['recall@5']:.4f}          | {summary['vector']['mrr']:.4f}")
    print(f"{'Hybrid RRF (k=60)':<25} | {summary['hybrid_rrf']['recall@5']:.4f}          | {summary['hybrid_rrf']['mrr']:.4f}")
    print("=" * 65)
    print(f"Metrics saved to {out_path}\n")


if __name__ == "__main__":
    evaluate_retrieval()
