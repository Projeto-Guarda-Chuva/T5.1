import os
import json
from datetime import date, datetime
from pathlib import Path

import pytest


os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("PROGRAMADOR_ATUACAO_BASE_URL", "http://programador.local")
os.environ.setdefault(
    "SECRET_KEY",
    "change-me-in-production-use-a-long-random-string",
)


_RESULTS_PATH = Path(__file__).resolve().parent / "results" / "last_run.json"
_RUN_RESULTS: dict = {
    "generated_at": None,
    "tests": [],
    "collection_errors": [],
}


def _jsonable(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return {
            "type": "bytes",
            "length": len(value),
        }
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return repr(value)


@pytest.fixture
def case_log(request):
    payload = {
        "nodeid": request.node.nodeid,
        "input": None,
        "output": None,
        "notes": [],
    }
    request.node._case_log_payload = payload
    return payload


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    payload = getattr(
        item,
        "_case_log_payload",
        {
            "nodeid": item.nodeid,
            "input": None,
            "output": None,
            "notes": [],
        },
    )
    result = {
        "nodeid": item.nodeid,
        "status": report.outcome,
        "input": _jsonable(payload.get("input")),
        "output": _jsonable(payload.get("output")),
        "notes": _jsonable(payload.get("notes", [])),
    }

    if report.failed:
        result["error_type"] = call.excinfo.typename if call.excinfo else "AssertionError"
        result["error"] = str(call.excinfo.value) if call.excinfo else str(report.longrepr)
        result["traceback"] = str(report.longrepr)

    _RUN_RESULTS["tests"].append(result)


def pytest_collectreport(report):
    if not report.failed:
        return

    _RUN_RESULTS["collection_errors"].append(
        {
            "nodeid": report.nodeid,
            "outcome": report.outcome,
            "error": str(report.longrepr),
        }
    )


def pytest_sessionfinish(session, exitstatus):
    _RUN_RESULTS["generated_at"] = datetime.utcnow().isoformat() + "Z"
    _RUN_RESULTS["exitstatus"] = exitstatus
    _RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RESULTS_PATH.write_text(
        json.dumps(_jsonable(_RUN_RESULTS), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
