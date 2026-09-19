import json
from pathlib import Path
import sqlite3

from scripts import preflight_demo as preflight


def test_database_check_is_read_only_and_rejects_missing_or_empty_database(tmp_path):
    missing = tmp_path / "missing.db"
    assert not preflight.check_database(missing)
    assert not missing.exists()
    path = tmp_path / "demo.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE app_meta(key TEXT, value TEXT);
            INSERT INTO app_meta VALUES ('schema_version', '0.2');
            CREATE TABLE sources(source_id TEXT, name TEXT);
            CREATE TABLE notices(notice_id INTEGER, source_id TEXT, title TEXT,
                current_content_hash TEXT, publication_date TEXT, canonical_url TEXT);
            CREATE TABLE notice_versions(notice_id INTEGER, version_id INTEGER,
                raw_text TEXT, content_hash TEXT);
        """)
    assert not preflight.check_database(path)
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO sources VALUES ('source', 'Official source')")
        conn.execute("INSERT INTO notices VALUES (1, 'source', 'Title', 'hash', NULL, NULL)")
        conn.execute("INSERT INTO notice_versions VALUES (1, 1, 'Notice text', 'hash')")
    before = path.read_bytes()
    assert preflight.check_database(path)
    assert path.read_bytes() == before


def test_database_path_honors_environment_override_and_project_root(tmp_path):
    assert preflight.database_path("sqlite:///./unitrust.db", tmp_path) == tmp_path / "unitrust.db"
    absolute = tmp_path / "isolated.db"
    assert preflight.database_path(f"sqlite:///{absolute}") == absolute


def test_reviewed_annotations_empty_invalid_and_valid(tmp_path):
    assert not preflight.check_annotations(tmp_path)
    path = tmp_path / "annotation.json"
    path.write_text('{"not": "an annotation"}', encoding="utf-8")
    assert not preflight.check_annotations(tmp_path)
    data = {
        "annotation_status": "REVIEWED", "annotator_id": "test",
        "notice_id": 1, "version_id": 1,
        "source": {"source_id": "test", "name": "Test fixture"},
        "title": "Fixture", "raw_text": "Submit form",
        "observed_at": "2026-01-01T00:00:00Z", "url": "https://example.test/fixture",
        "content_hash": "fixture", "obligations": [{
            "obligation_id": "fixture-1", "action": {"action_type": "submit", "text": "Submit form"},
        }],
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    before = path.read_bytes()
    assert preflight.check_annotations(tmp_path)
    assert path.read_bytes() == before
    data["annotation_status"] = "DRAFT"
    path.write_text(json.dumps(data), encoding="utf-8")
    assert not preflight.check_annotations(tmp_path)


def test_preflight_never_imports_heavy_model_packages(monkeypatch):
    imported = []
    discovered = []
    monkeypatch.setattr(preflight.importlib, "import_module", lambda name: imported.append(name))
    monkeypatch.setattr(preflight.importlib.util, "find_spec", lambda name: discovered.append(name) or object())
    assert preflight.check_imports()
    assert "sentence_transformers" not in imported
    assert "torch" not in imported
    assert {"sentence_transformers", "torch", "streamlit"} <= set(discovered)


def test_missing_model_fails_without_loading_it(monkeypatch):
    from app.retrieval import model_cache

    def missing():
        raise FileNotFoundError("required local weights are missing")

    monkeypatch.setattr(model_cache, "resolve_local_model", missing)
    assert not preflight.check_model_cache()
    monkeypatch.setattr(model_cache, "resolve_local_model", lambda: Path("snapshot"))
    assert preflight.check_model_cache()


def test_occupied_port_reports_owner_without_any_kill(monkeypatch, capsys):
    class OccupiedSocket:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def setsockopt(self, *args):
            pass

        def bind(self, address):
            raise OSError("occupied")

    monkeypatch.setattr(preflight.socket, "socket", lambda *args: OccupiedSocket())
    monkeypatch.setattr(preflight, "port_owners", lambda port: [{"ProcessId": 123, "Name": "other.exe"}])
    assert not preflight.check_port_free(8000)
    output = capsys.readouterr().out
    assert "PID 123: other.exe" in output


def test_preflight_failure_exit_code(monkeypatch):
    monkeypatch.setattr(preflight, "check_database", lambda path: False)
    monkeypatch.setattr(preflight, "check_imports", lambda: True)
    monkeypatch.setattr(preflight, "check_annotations", lambda path: True)
    monkeypatch.setattr(preflight, "check_model_cache", lambda: True)
    monkeypatch.setattr(preflight, "check_port_free", lambda port: True)
    assert preflight.main() == 1
