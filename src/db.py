"""Acceso a SQLite, geografía ficticia y utilidades de tiempo."""
import json
import sqlite3
from contextlib import contextmanager
from functools import lru_cache

from . import config

ZONES = ["Centro", "Norte", "Sur", "Oriente", "Poniente", "Industrial"]
DEPOT_ZONE = "Industrial"

_D = {
    ("Industrial", "Centro"): 8, ("Industrial", "Norte"): 12, ("Industrial", "Sur"): 14,
    ("Industrial", "Oriente"): 10, ("Industrial", "Poniente"): 6,
    ("Centro", "Norte"): 6, ("Centro", "Sur"): 7, ("Centro", "Oriente"): 5,
    ("Centro", "Poniente"): 5, ("Norte", "Sur"): 13, ("Norte", "Oriente"): 8,
    ("Norte", "Poniente"): 9, ("Sur", "Oriente"): 9, ("Sur", "Poniente"): 10,
    ("Oriente", "Poniente"): 10,
}
DISTANCES = {}
for (a, b), km in _D.items():
    DISTANCES[(a, b)] = km
    DISTANCES[(b, a)] = km
for z in ZONES:
    DISTANCES[(z, z)] = 2  # reparto dentro de la misma zona

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY, plate TEXT, capacity_kg INTEGER, status TEXT,
    driver TEXT, depot_zone TEXT, shift_end INTEGER);
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY, name TEXT, tier TEXT, contact TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY, client_id INTEGER, zone TEXT, weight_kg INTEGER,
    priority INTEGER, window_start INTEGER, window_end INTEGER,
    status TEXT, attempts INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, truck_id INTEGER,
    seq INTEGER, eta INTEGER, status TEXT);
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, type TEXT, truck_id INTEGER,
    order_id INTEGER, client_id INTEGER, description TEXT, resolution TEXT,
    strategy TEXT);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(config.db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_schema(reset: bool = False):
    with connect() as c:
        if reset:
            for t in ("meta", "trucks", "clients", "orders", "assignments", "incidents"):
                c.execute(f"DROP TABLE IF EXISTS {t}")
        c.executescript(SCHEMA)


def rows(sql: str, params=()) -> list[dict]:
    with connect() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def one(sql: str, params=()) -> dict | None:
    r = rows(sql, params)
    return r[0] if r else None


def execute(sql: str, params=()) -> int:
    with connect() as c:
        cur = c.execute(sql, params)
        return cur.lastrowid


# ---------- tiempo ----------
def mins(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def hm(minutes: int) -> str:
    return f"{int(minutes) // 60:02d}:{int(minutes) % 60:02d}"


def get_now() -> int:
    r = one("SELECT value FROM meta WHERE key='sim_now'")
    return int(r["value"]) if r else config.SHIFT_START


def set_now(minutes: int):
    execute("INSERT OR REPLACE INTO meta(key,value) VALUES('sim_now',?)", (str(int(minutes)),))


# ---------- tráfico y viaje ----------
@lru_cache(maxsize=1)
def _traffic() -> dict:
    return json.loads(config.traffic_path().read_text(encoding="utf-8"))


def traffic_multiplier(zone: str, minute: int) -> float:
    h = int(minute) // 60
    bucket = "06-10" if h < 10 else "10-16" if h < 16 else "16-20"
    return float(_traffic().get(zone, {}).get(bucket, 1.0))


def travel_minutes(origin: str, dest: str, minute: int) -> int:
    km = DISTANCES[(origin, dest)]
    base = km / config.BASE_SPEED_KMH * 60
    return max(1, round(base * traffic_multiplier(dest, minute)))
