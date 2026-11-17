import re
from decimal import Decimal
from typing import Any


def extract_numbers_from_sql_rows(rows: list[dict[str, Any]]) -> set[str]:
    """Extract flattened string representation of numeric values from SQL rows."""
    nums: set[str] = set()
    for row in rows:
        for val in row.values():
            if val is None:
                continue
            if isinstance(val, (int, float, Decimal)):
                s = str(val).rstrip("0").rstrip(".") if "." in str(val) else str(val)
                nums.add(s)
                # Add integer portion for decimals
                if "." in str(val):
                    nums.add(str(val).split(".")[0])
            elif isinstance(val, str) and re.match(r"^\d+(?:\.\d+)?$", val.strip()):
                nums.add(val.strip())
    return nums


def extract_key_metrics_from_text(text: str) -> list[str]:
    """Extract significant quantitative metric values from answer prose."""
    # Match large integers or decimals (>= 10 or with decimal points), ignoring section markers
    raw_matches = re.findall(r"(?:R\$\s*|\$)?(\b\d{1,3}(?:[,\.]\d{3})*(?:\.\d+)?\b)", text)
    cleaned: list[str] = []
    for m in raw_matches:
        norm = m.replace(",", "")
        # Filter out trivial dates or citation indicators (e.g. 2024, 1, 2, 3)
        try:
            val = float(norm)
            if val >= 10.0 and val not in {2023.0, 2024.0, 2025.0, 2026.0}:
                cleaned.append(norm)
        except ValueError:
            continue
    return cleaned


def verify_response(
    answer: str,
    cited_chunk_ids: list[str],
    valid_chunk_ids: set[str],
    sql_rows: list[dict[str, Any]] | None = None,
) -> tuple[bool, str]:
    """Verify that cited chunk IDs exist and SQL numerical figures match database output."""
    # 1. Chunk ID Existence Verification
    for cid in cited_chunk_ids:
        if cid not in valid_chunk_ids:
            # Verification prevents hallucinated citations
            return False, f"Cited chunk ID '{cid}' does not exist in retrieved sources."

    # 2. Numerical Consistency Verification
    if sql_rows is not None and len(sql_rows) > 0:
        sql_nums = extract_numbers_from_sql_rows(sql_rows)
        if sql_nums:
            answer_metrics = extract_key_metrics_from_text(answer)
            # Check if at least one key metric from the SQL result appears in the text
            has_matching_sql_metric = any(
                any(s_num in m or m in s_num for s_num in sql_nums)
                for m in answer_metrics
            )
            # If answer quoted metrics but none matched SQL outputs, flag discrepancy
            if answer_metrics and not has_matching_sql_metric:
                sql_preview = sorted(list(sql_nums))[:5]
                return (
                    False,
                    f"Numerical inconsistency: Metric in answer does not match SQL: {sql_preview}",
                )

    return True, "Verification passed"
