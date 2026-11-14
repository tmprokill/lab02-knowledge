"""Валідатор рішень агента (Guardrail)."""
from agent.errors import DecisionError

ALLOWED_ACTIONS = {"search_knowledge", "read_note", "write_note", "finish"}

def validate_decision(decision: dict) -> None:
    """Перевіряє коректність рішення моделі за білим списком та типами аргументів."""
    if not isinstance(decision, dict):
        raise DecisionError("Рішення має бути валідним JSON-об'єктом")

    action = decision.get("action")
    if not action or action not in ALLOWED_ACTIONS:
        raise DecisionError(f"Невідома дія '{action}'. Дозволені дії: {sorted(ALLOWED_ACTIONS)}")

    args = decision.get("args")
    if not isinstance(args, dict):
        raise DecisionError(f"Поле 'args' для дії '{action}' має бути JSON-об'єктом")

    if action == "search_knowledge":
        query = args.get("query")
        if not query or not isinstance(query, str) or not query.strip():
            raise DecisionError("Дія 'search_knowledge' вимагає непорожній рядковий аргумент 'query'")

    elif action == "read_note":
        rel_path = args.get("rel_path")
        if not rel_path or not isinstance(rel_path, str) or not rel_path.strip():
            raise DecisionError("Дія 'read_note' вимагає непорожній рядковий аргумент 'rel_path'")

    elif action == "write_note":
        title = args.get("title")
        content = args.get("content")
        if not title or not isinstance(title, str) or not content or not isinstance(content, str):
            raise DecisionError("Дія 'write_note' вимагає непорожні аргументи 'title' та 'content'")

    elif action == "finish":
        answer = args.get("answer")
        if not answer or not isinstance(answer, str) or not answer.strip():
            raise DecisionError("Дія 'finish' вимагає непорожній рядковий аргумент 'answer'")
