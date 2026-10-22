# Evidencia de pruebas de escenarios

Generado con `python scripts/generate_evidence.py --llm ollama --embeddings ollama`.

Cada archivo muestra el razonamiento paso a paso del agente (nodo por nodo) y un resumen verificable del estado final. Las mismas condiciones se verifican automáticamente en `tests/test_scenarios.py`.

- [escenario_0_jornada_normal](escenario_0_jornada_normal.md)
- [escenario_1_averia](escenario_1_averia.md)
- [escenario_2_vip_urgente](escenario_2_vip_urgente.md)
- [escenario_3_entrega_fallida](escenario_3_entrega_fallida.md)
- [escenario_4_memoria_larga](escenario_4_memoria_larga.md)
- [escenario_5_cadena_y_memoria_corta](escenario_5_cadena_y_memoria_corta.md)
- [escenario_6_llm_caido](escenario_6_llm_caido.md)
- [escenario_7_eventos_ambiguos](escenario_7_eventos_ambiguos.md)
- [escenario_8_plan_imposible](escenario_8_plan_imposible.md)
