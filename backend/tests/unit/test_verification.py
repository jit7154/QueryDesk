from app.services.verification.checks import (
    extract_numbers_from_sql_rows,
    verify_response,
)


def test_verify_response_valid_citations() -> None:
    """Answer with valid chunk citations must pass verification."""
    answer = "Under Section 7.2 of the supplier agreement, late delivery incurs a 4% penalty."
    cited = ["chunk_123", "chunk_456"]
    valid = {"chunk_123", "chunk_456", "chunk_789"}
    passed, msg = verify_response(answer, cited, valid)
    assert passed is True
    assert "passed" in msg


def test_verify_response_invalid_chunk_citation() -> None:
    """Answer citing hallucinated chunk IDs must fail verification."""
    answer = "According to our contract terms, refunds are 100% covered."
    cited = ["chunk_unknown_999"]
    valid = {"chunk_123", "chunk_456"}
    passed, msg = verify_response(answer, cited, valid)
    assert passed is False
    assert "chunk_unknown_999" in msg


def test_verify_response_sql_numerical_match() -> None:
    """Answer containing numbers matching SQL output must pass verification."""
    answer = "Seller Apex generated a total of R$ 123,304.83 across 2,033 orders."
    sql_rows = [{"total_revenue": 123304.83, "order_count": 2033}]
    passed, msg = verify_response(
        answer=answer,
        cited_chunk_ids=[],
        valid_chunk_ids=set(),
        sql_rows=sql_rows,
    )
    assert passed is True


def test_verify_response_sql_numerical_mismatch() -> None:
    """Answer with hallucinated numbers deviating from SQL results must fail verification."""
    answer = "The total revenue was R$ 999,999.00."
    sql_rows = [{"total_revenue": 123304.83}]
    passed, msg = verify_response(
        answer=answer,
        cited_chunk_ids=[],
        valid_chunk_ids=set(),
        sql_rows=sql_rows,
    )
    assert passed is False
    assert "Numerical inconsistency" in msg


def test_extract_numbers_from_sql_rows() -> None:
    """Numbers from SQL rows must be properly extracted and formatted."""
    rows = [{"count": 99441, "amount": 123.45, "status": "delivered", "id": "S123"}]
    nums = extract_numbers_from_sql_rows(rows)
    assert "99441" in nums
    assert "123.45" in nums
    assert "123" in nums  # integer part
