"""Головний цикл керування агента з базою знань."""
from datetime import datetime
import json
from pathlib import Path
from agent.errors import DecisionError
from agent.state import AgentState
from agent.validator import validate_decision
from agent.reasoning import decide_next_step
from agent.environment import KnowledgeEnvironment

MAX_STEPS = 6
MAX_LLM_CALLS = 8

def run_agent_loop(
    goal: str,
    env: KnowledgeEnvironment,
    decision_fn=decide_next_step,
    max_steps: int = MAX_STEPS,
    max_llm_calls: int = MAX_LLM_CALLS,
) -> AgentState:
    """Виконує повний цикл Observe -> Reason -> Act -> Evaluate."""
    state = AgentState(goal=goal)

    print(f"\n[Agent] Старт мети: {goal}")

    while not state.finished:
        # Перевірка умов зупинки
        if state.step >= max_steps:
            state.finished = True
            state.stop_reason = "max_steps"
            state.final_answer = "Агент зупинився через досягнення граничного ліміту кроків MAX_STEPS."
            print(f"[Agent Warning] Зупинка за MAX_STEPS ({max_steps})")
            break

        if state.llm_calls >= max_llm_calls:
            state.finished = True
            state.stop_reason = "max_llm_calls"
            state.final_answer = "Агент зупинився через вичерпання бюджету звернень до моделі MAX_LLM_CALLS."
            print(f"[Agent Warning] Зупинка за MAX_LLM_CALLS ({max_llm_calls})")
            break

        state.step += 1
        state.llm_calls += 1
        print(f"\n--- КРОК {state.step} (LLM виклик #{state.llm_calls}) ---")

        # REASON
        try:
            decision = decision_fn(state)
        except DecisionError as e:
            err_obs = f"ERROR: Помилка прийняття рішень: {e}"
            state.observations.append(err_obs)
            state.trace.append({
                "step": state.step,
                "thought": "Decision parsing failed",
                "action": "error",
                "args": {},
                "observation": err_obs,
            })
            continue

        thought = decision.get("thought", "")
        action = decision.get("action", "")
        args = decision.get("args", {})
        print(f"Thought: {thought}")
        print(f"Action:  {action}({args})")

        # VALIDATE
        try:
            validate_decision(decision)
        except DecisionError as e:
            err_obs = f"ERROR_VALIDATION: Валідатор відхилив рішення: {e}"
            print(f"[Validator Guardrail] {err_obs}")
            state.observations.append(err_obs)
            state.trace.append({
                "step": state.step,
                "thought": thought,
                "action": action,
                "args": args,
                "observation": err_obs,
            })
            continue

        # ACT & DISPATCH
        if action == "finish":
            state.finished = True
            state.stop_reason = "finish"
            state.final_answer = args.get("answer", "")
            state.trace.append({
                "step": state.step,
                "thought": thought,
                "action": "finish",
                "args": args,
                "observation": "FINISHED",
            })
            print("[Agent] Успішне завершення мети.")
            break

        elif action == "search_knowledge":
            obs = env.search_knowledge(query=args["query"], tag=args.get("tag"))

        elif action == "read_note":
            obs = env.read_note(rel_path=args["rel_path"])

        elif action == "write_note":
            # Якщо викликано з терміналу — питаємо підтвердження користувача
            obs = env.write_note(title=args["title"], content=args["content"], confirm=True)

        else:
            obs = f"ERROR: Непідтримувана дія {action}"

        # EVALUATE
        state.observations.append(obs)
        state.trace.append({
            "step": state.step,
            "thought": thought,
            "action": action,
            "args": args,
            "observation": obs[:300] + ("..." if len(obs) > 300 else ""),
        })

    # Збереження журналу трасування
    _save_trace(state)
    return state

def _save_trace(state: AgentState, trace_dir: str = "traces") -> str:
    Path(trace_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(trace_dir) / f"trace_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": ts,
            "goal": state.goal,
            "step": state.step,
            "llm_calls": state.llm_calls,
            "stop_reason": state.stop_reason,
            "final_answer": state.final_answer,
            "trace": state.trace,
        }, f, indent=2, ensure_ascii=False)
    print(f"[Trace] Трасування збережено в: {path}")
    return str(path)
