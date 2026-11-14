import pytest
from agent.validator import validate_decision
from agent.errors import DecisionError

def test_validator_allowed_actions():
    validate_decision({"action": "search_knowledge", "args": {"query": "test query"}})
    validate_decision({"action": "read_note", "args": {"rel_path": "Architecture/note.md"}})
    validate_decision({"action": "finish", "args": {"answer": "done"}})

def test_validator_reject_unknown_action():
    with pytest.raises(DecisionError, match="Невідома дія"):
        validate_decision({"action": "drop_database", "args": {}})

def test_validator_reject_empty_query():
    with pytest.raises(DecisionError, match="непорожній рядковий аргумент 'query'"):
        validate_decision({"action": "search_knowledge", "args": {"query": ""}})
