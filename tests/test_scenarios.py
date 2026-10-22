"""Escenarios end-to-end del agente (IE5, IE7). Sin LLM ni red."""
from src import db
from tests.scenarios import scenarios as sc


def test_s0_jornada_normal(make_agent):
    res, info = sc.s0_jornada_normal(make_agent())
    assert res[0][1]["outcome"] == "ok"
    assert info["asignaciones"] == 25 and info["camiones"] >= 2


def test_s1_averia_reasigna(make_agent):
    res, info = sc.s1_averia(make_agent())
    assert info["camion3"] == "averiado"
    assert info["asignaciones_camion3"] == 0          # nadie queda asignado al camión averiado
    assert info["asignaciones_total"] == 25 - info["entregados"]   # nada se pierde
    assert res[-1][1]["notifications"], "debe avisar a los clientes afectados"
    assert db.one("SELECT COUNT(*) n FROM incidents WHERE type='averia' AND truck_id=3")["n"] >= 1


def test_s2_vip_prioridad_y_hora_limite(make_agent):
    res, info = sc.s2_vip_urgente(make_agent())
    assert info["prioridad"] == 4
    assert info["eta"] <= 12 * 60
    assert res[-1][1]["outcome"] in ("ok", "escalated")
    assert any(n["kind"] == "vip" for n in res[-1][1]["notifications"])


def test_s3_reintento_y_escalamiento(make_agent):
    res, info = sc.s3_entrega_fallida(make_agent())
    first, second = res[1][1], res[2][1]
    assert first["decision"]["kind"] == "fallida_hoy"        # 1er fallo: reintento el mismo día
    assert second["decision"]["kind"] == "fallida_escalada"  # 2.º fallo: escalamiento (política)
    assert info["intentos"] == 2 and info["estado_final"] == "fallido"
    assert second["escalated"] is True


def test_s4_memoria_larga_recupera_incidente(make_agent):
    res, info = sc.s4_memoria_larga(make_agent())
    assert info["recuerdos"] >= 1
    assert info["estrategia_recordada"] == "reasignar_a_mayor_capacidad"
    assert any("Memoria larga: incidente similar" in line for line in res[-1][1]["log"])


def test_s5_memoria_corta_cuenta_replanificaciones(make_agent):
    agent = make_agent("jornada-s5")
    res, info = sc.s5_cadena_y_memoria_corta(agent)
    assert info["camion3"] == "averiado"
    assert info["eventos_en_memoria"] == 4
    assert info["replans_hoy"] == 3
    last = res[-1][1]
    assert last["outcome"] == "escalated"
    assert any("inestabilidad" in line for line in last["log"])


def test_s5b_estado_persiste_tras_reiniciar(make_agent):
    sc.s5_cadena_y_memoria_corta(make_agent("jornada-persist"))
    nuevo = make_agent("jornada-persist")      # "otro proceso", mismo thread_id
    assert len(nuevo.state()["history"]) == 4
    otro = make_agent("otra-jornada")           # otro thread_id: memoria vacía
    assert otro.state() == {}


def test_s6_llm_caido_usa_reglas(make_agent, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "")
    res, info = sc.s6_llm_caido(make_agent())
    assert "reglas" in info["fuente"]
    assert res[-1][1]["classification"]["tipo"] == "averia"
    assert res[-1][1]["outcome"] == "ok"


def test_s7_eventos_ambiguos(make_agent):
    res, info = sc.s7_eventos_ambiguos(make_agent())
    assert info["resultados"] == ["escalated", "needs_info", "needs_info"]
    assert db.one("SELECT status FROM trucks WHERE id=99") is None   # nada se inventó
    assert res[3][1]["classification"].get("invalid_truck") == 99


def test_s8_plan_imposible_escala(make_agent):
    res, info = sc.s8_plan_imposible(make_agent())
    last = res[-1][1]
    assert last["escalated"] is True
    assert info["violaciones"] > 0
    assert any("no pueden cumplir su ventana" in line for line in last["log"])
