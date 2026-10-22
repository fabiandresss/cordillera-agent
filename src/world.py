"""Operaciones sobre el «mundo» simulado: regenerar datos y memoria (usado por la API)."""
import importlib.util

from . import config, memory

_SEED = config.ROOT / "data" / "seed.py"


def reseed() -> None:
    """Regenera la BD sintética, borra salidas previas y reconstruye la memoria semántica."""
    spec = importlib.util.spec_from_file_location("cordillera_seed", _SEED)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.build()
    for f in ("outbox.jsonl", "escalamientos.jsonl"):
        (config.output_dir() / f).unlink(missing_ok=True)
    memory.index_all(force=True)
