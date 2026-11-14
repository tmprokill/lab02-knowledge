from agent.state import AgentState
from agent.loop import run_agent_loop

class DummyEnv:
    def search_knowledge(self, query, tag=None):
        return '<fragment reference="[[Doc#Section]]">Знайдено опис SmartLease.</fragment>'

    def read_note(self, rel_path):
        return "Повний текст нотатки"

    def write_note(self, title, content, confirm=True):
        return "SUCCESS"

def test_loop_finish():
    calls = 0
    def mock_decision(state: AgentState):
        nonlocal calls
        calls += 1
        return {"action": "finish", "args": {"answer": "Остаточна відповідь"}}

    state = run_agent_loop("Тестовий запит", env=DummyEnv(), decision_fn=mock_decision)
    assert state.finished is True
    assert state.stop_reason == "finish"
    assert state.final_answer == "Остаточна відповідь"
    assert calls == 1

def test_loop_max_steps():
    def infinite_decision(state: AgentState):
        return {"action": "search_knowledge", "args": {"query": "loop"}}

    state = run_agent_loop("Запит зациклення", env=DummyEnv(), decision_fn=infinite_decision, max_steps=3)
    assert state.finished is True
    assert state.stop_reason == "max_steps"
    assert state.step == 3
