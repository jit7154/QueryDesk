from app.schemas.document import ChunkInfo
from app.services.retrieval.rrf import reciprocal_rank_fusion


def make_chunk(cid: str, name: str, score: float = 0.0) -> ChunkInfo:
    return ChunkInfo(
        chunk_id=cid,
        document_name=name,
        section_title="Section 1.0",
        page_number=1,
        chunk_index=0,
        content=f"Content for {cid}",
        score=score,
    )


def test_rrf_empty_lists() -> None:
    """Empty inputs should yield empty fused output."""
    result = reciprocal_rank_fusion([], k=60, top_k=5)
    assert result == []

    result2 = reciprocal_rank_fusion([[], []], k=60, top_k=5)
    assert result2 == []


def test_rrf_combines_ranks() -> None:
    """Items present across multiple lists receive higher combined RRF scores."""
    # List 1: chunk_A (rank 1), chunk_B (rank 2)
    # List 2: chunk_B (rank 1), chunk_C (rank 2)
    list1 = [make_chunk("chunk_A", "docA"), make_chunk("chunk_B", "docB")]
    list2 = [make_chunk("chunk_B", "docB"), make_chunk("chunk_C", "docC")]

    fused = reciprocal_rank_fusion([list1, list2], k=60, top_k=3)

    assert len(fused) == 3
    # chunk_B appears in both: 1/(60+2) + 1/(60+1) = 0.0161 + 0.01639 = 0.0325
    # chunk_A appears only in list 1: 1/(60+1) = 0.01639
    # chunk_C appears only in list 2: 1/(60+2) = 0.01612
    assert fused[0].chunk_id == "chunk_B"
    assert fused[1].chunk_id == "chunk_A"
    assert fused[2].chunk_id == "chunk_C"


def test_rrf_top_k_cutoff() -> None:
    """RRF must limit output count to specified top_k."""
    list1 = [make_chunk(f"c_{i}", f"doc_{i}") for i in range(10)]
    fused = reciprocal_rank_fusion([list1], k=60, top_k=4)
    assert len(fused) == 4
    assert fused[0].chunk_id == "c_0"
    assert fused[3].chunk_id == "c_3"
