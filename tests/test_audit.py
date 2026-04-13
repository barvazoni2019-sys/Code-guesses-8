from app.audit import AuditLogger


def test_audit_logger_log_and_tail(tmp_path) -> None:
    logger = AuditLogger(path=str(tmp_path / "audit.log"))
    logger.log({"request_id": "r1", "path": "/health", "status_code": 200})
    logger.log({"request_id": "r2", "path": "/analyze", "status_code": 200})

    rows = logger.tail(1)
    assert len(rows) == 1
    assert rows[0]["request_id"] == "r2"
