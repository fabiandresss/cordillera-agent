import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def load_seed():
    spec = importlib.util.spec_from_file_location("cordillera_seed", ROOT / "data" / "seed.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def world(tmp_path, monkeypatch):
    """Mundo aislado: BD, Chroma y salidas en un directorio temporal; sin LLM ni red."""
    monkeypatch.setenv("CORDILLERA_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("CORDILLERA_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setenv("LLM_PROVIDER", "rules")
    monkeypatch.setenv("EMBEDDINGS_PROVIDER", "fake")
    monkeypatch.setenv("SIMILARITY_THRESHOLD", "0.25")
    load_seed().build()
    return tmp_path


@pytest.fixture
def make_agent(world):
    from src.agent import DispatchAgent

    def _make(thread_id="test-jornada", **kw):
        return DispatchAgent(thread_id=thread_id, **kw)

    return _make
