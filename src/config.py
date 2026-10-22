"""Configuración central. Las rutas y proveedores se leen en cada llamada
para que las pruebas puedan redirigirlos con variables de entorno."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# Parámetros de negocio (documentados en docs/planificacion.md)
SERVICE_MIN = 10          # minutos de servicio por parada
BASE_SPEED_KMH = 40       # velocidad base sin tráfico
SHIFT_START = 8 * 60      # 08:00
SHIFT_END = 18 * 60       # 18:00
MAX_FAILED_ATTEMPTS = 2   # política: al 2.º intento fallido se escala
MAX_REPLANS = 3           # reintentos de reparación antes de escalar
JORNADA = "2026-10-26"


def _dir(env: str, default: Path) -> Path:
    p = Path(os.getenv(env, default))
    p.mkdir(parents=True, exist_ok=True)
    return p


def state_dir() -> Path:
    """BD SQLite, Chroma y checkpoints (se regeneran con seed.py)."""
    return _dir("CORDILLERA_STATE_DIR", ROOT / "data" / "runtime")


def output_dir() -> Path:
    return _dir("CORDILLERA_OUTPUT_DIR", ROOT / "outputs")


def db_path() -> Path:
    return state_dir() / "cordillera.db"


def checkpoint_path() -> Path:
    return state_dir() / "checkpoints.db"


def chroma_dir() -> Path:
    return state_dir() / "chroma"


def policies_dir() -> Path:
    return ROOT / "data" / "politicas"


def traffic_path() -> Path:
    return ROOT / "data" / "traffic.json"


def llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "ollama").lower()


def embeddings_provider() -> str:
    return os.getenv("EMBEDDINGS_PROVIDER", "ollama").lower()


def similarity_threshold() -> float:
    """Umbral de similitud coseno para aceptar un recuerdo (calibrado en docs/evidencia)."""
    return float(os.getenv("SIMILARITY_THRESHOLD", "0.60"))
