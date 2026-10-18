"""The navigation guides must stay true: links resolve, referenced files and functions exist, every
functional requirement has a row, and the lifecycle diagram is the real transition table."""

import csv
import re
from pathlib import Path

import pytest

from src.persistence import lifecycle

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
GUIDES = [DOCS / "START-HERE.md", DOCS / "ARCHITECTURE.md", DOCS / "REQUIREMENTS-MAP.md"]
FILE_EXTENSIONS = {"py", "sql", "html", "css", "csv", "md", "yml", "json"}
CODE_DIRS = [DOCS, ROOT / "src", ROOT / "tests", ROOT / "scripts", ROOT / "tools", ROOT / "performance",
             ROOT / ".github"]


def text(path):
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("guide", [*GUIDES, ROOT / "README.md"], ids=lambda p: p.name)
def test_every_relative_link_resolves(guide):
    broken = []
    for target in re.findall(r"\]\(([^)]+)\)", text(guide)):
        if target.startswith(("http", "#", "mailto:")):
            continue
        if not (guide.parent / target.split("#")[0]).resolve().exists():
            broken.append(target)
    assert not broken, f"{guide.name}: broken links {broken}"


def find_file(name):
    """A file named in backticks: a path from the repo root, or a bare file name found anywhere in the code."""
    if (ROOT / name).exists() or (DOCS / name).exists():
        return True
    return any(next(directory.rglob(Path(name).name), None) for directory in CODE_DIRS if directory.exists())


@pytest.mark.parametrize("guide", GUIDES, ids=lambda p: p.name)
def test_every_file_named_in_backticks_exists(guide):
    missing = []
    for token in set(re.findall(r"`([^`\s]+)`", text(guide))):
        token = token.rstrip(",.;:")
        if token.startswith("/"):  # a URL path such as /manager/requests.csv, not a file
            continue
        if re.fullmatch(r"[\w./-]+\.(py|sql|html|css|csv|md|yml|json)", token) and not find_file(token):
            missing.append(token)
    assert not missing, f"{guide.name}: files that do not exist {missing}"


def test_service_functions_named_as_module_dot_function_exist():
    modules = {p.stem: text(p) for p in (ROOT / "src" / "persistence").glob("*.py")}
    modules["app"] = text(ROOT / "src" / "web" / "app.py")
    missing = []
    for guide in GUIDES:
        for module, symbol in re.findall(r"`(\w+)\.(\w+)`", text(guide)):
            if symbol in FILE_EXTENSIONS:  # `workflow.py` is a file, checked elsewhere
                continue
            if module in modules and not re.search(rf"(def|class)\s+{symbol}\b|^{symbol}\s*[=:]",
                                                   modules[module], re.MULTILINE):
                missing.append(f"{module}.{symbol}")
    assert not missing, f"named functions not found: {missing}"


def test_every_functional_requirement_has_a_row_in_the_map():
    with (DOCS / "requirements" / "functional-requirements.csv").open(encoding="utf-8", newline="") as handle:
        ids = [row[0] for row in csv.reader(handle) if row and row[0].startswith("FR-")]
    mapped = set(re.findall(r"^\| (FR-\d{3}) \|", text(DOCS / "REQUIREMENTS-MAP.md"), re.MULTILINE))
    assert len(ids) == 26 and set(ids) == mapped, f"missing rows: {sorted(set(ids) - mapped)}"


def test_the_lifecycle_diagram_is_the_real_transition_table():
    diagram = text(DOCS / "ARCHITECTURE.md").split("stateDiagram-v2")[1].split("```")[0]
    names = {"InProgress": "In Progress", "OnHold": "On Hold"}
    drawn = set()
    for source, target in re.findall(r"^\s*(\w+|\[\*\]) --> (\w+|\[\*\])", diagram, re.MULTILINE):
        if "[*]" in (source, target):
            continue
        drawn.add((names.get(source, source), names.get(target, target)))
    real = {(src, dst) for src, targets in lifecycle.TRANSITIONS.items() for dst in targets}
    assert drawn == real, f"only in diagram: {sorted(drawn - real)}; only in code: {sorted(real - drawn)}"


def test_the_data_diagram_lists_every_table():
    schema = text(ROOT / "src" / "persistence" / "schema.sql") + text(ROOT / "src" / "persistence" / "migrations.py")
    tables = set(re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)", schema))
    documented = set(re.findall(r"^\| `(\w+)`", text(DOCS / "ARCHITECTURE.md"), re.MULTILINE))
    documented |= {part.strip(" `") for line in text(DOCS / "ARCHITECTURE.md").splitlines()
                   if line.startswith("| `outbox_events`") for part in line.split("|")[1].split(",")}
    assert tables <= documented, f"tables missing from ARCHITECTURE.md: {sorted(tables - documented)}"
