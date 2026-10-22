from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from src.qa_agent import ask, build_qa_agent


class ToolFake(GenericFakeChatModel):
    def bind_tools(self, tools, **kw):
        return self


def test_agente_conversacional_usa_herramientas(world):
    msgs = iter([
        AIMessage(content="", tool_calls=[{"name": "get_fleet_status", "args": {}, "id": "c1"}]),
        AIMessage(content="Hay 5 camiones registrados."),
    ])
    agent = build_qa_agent(model=ToolFake(messages=msgs))
    answer, used = ask(agent, "¿Cuántos camiones hay?")
    assert used == ["get_fleet_status"] and "5 camiones" in answer
