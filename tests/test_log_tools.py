"""The AI register validator that replaces line-level merging of a shared file."""

import importlib.util
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "ai_register.py"
HEADER = "ID,Date,Student,Tool,Engineering task,AI contribution,Human verification,Decision,Issues found\n"
ROW = "{id},2026-10-18,Test,Tool,task,did,checked,ok,none\n"


@pytest.fixture
def register(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("ai_register_under_test", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    legacy = tmp_path / "legacy.csv"
    legacy.write_text(HEADER + ROW.format(id="AI-001") + ROW.format(id="AI-002"), encoding="utf-8")
    records = tmp_path / "records"
    records.mkdir()
    monkeypatch.setattr(module, "LEGACY", legacy)
    monkeypatch.setattr(module, "RECORDS", records)
    return module, records


def test_valid_register_has_no_problems_and_next_id(register, capsys):
    module, records = register
    (records / "AI-003.csv").write_text(ROW.format(id="AI-003"), encoding="utf-8")
    assert module.main(["--check"]) == 0
    assert module.main(["--next"]) == 0
    assert capsys.readouterr().out.strip().endswith("AI-004")


def test_duplicate_id_between_legacy_and_record_is_reported(register, capsys):
    module, records = register
    (records / "AI-002.csv").write_text(ROW.format(id="AI-002"), encoding="utf-8")
    assert module.main(["--check"]) == 1
    assert "duplicate ID AI-002" in capsys.readouterr().out


def test_file_name_must_match_id_and_row_must_have_nine_columns(register, capsys):
    module, records = register
    (records / "AI-005.csv").write_text(ROW.format(id="AI-006"), encoding="utf-8")
    (records / "AI-007.csv").write_text("AI-007,2026-10-18,Test\n", encoding="utf-8")
    assert module.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert "expected 'AI-005'" in out and "3 columns, expected 9" in out


def test_combined_output_is_sorted_with_one_header(register, capsys):
    module, records = register
    (records / "AI-003.csv").write_text(ROW.format(id="AI-003"), encoding="utf-8")
    assert module.main([]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines[0].startswith("ID,") and [ln.split(",")[0] for ln in lines[1:]] == ["AI-001", "AI-002", "AI-003"]


def test_the_real_register_is_valid():
    spec = importlib.util.spec_from_file_location("ai_register_real", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main(["--check"]) == 0
