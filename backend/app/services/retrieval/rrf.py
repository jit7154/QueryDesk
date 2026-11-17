from app.schemas.document import ChunkInfo


def reciprocal_rank_fusion(
    ranked_lists: list[list[ChunkInfo]],
    k: int = 60,
    top_k: int = 5,
) -> list[ChunkInfo]:
    """Fuse multiple ranked lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    chunk_map: dict[str, ChunkInfo] = {}

    for rank_list in ranked_lists:
        for rank_idx, chunk in enumerate(rank_list):
            cid = chunk.chunk_id
            if cid not in chunk_map:
                chunk_map[cid] = chunk

            # k=60 prevents top ranks from dominating when lists vary in size and confidence
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + (rank_idx + 1)))

    sorted_cids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    fused_results: list[ChunkInfo] = []
    for cid in sorted_cids[:top_k]:
        base_chunk = chunk_map[cid]
        fused_results.append(
            ChunkInfo(
                chunk_id=base_chunk.chunk_id,
                document_name=base_chunk.document_name,
                section_title=base_chunk.section_title,
                page_number=base_chunk.page_number,
                chunk_index=base_chunk.chunk_index,
                content=base_chunk.content,
                score=scores[cid],
            )
        )

    return fused_results
