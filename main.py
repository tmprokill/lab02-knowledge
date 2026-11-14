"""CLI запуск агента з базою знань."""
import argparse
from dotenv import load_dotenv
from agent.environment import KnowledgeEnvironment
from agent.loop import run_agent_loop

def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv()
    parser = argparse.ArgumentParser(description="SmartLease Knowledge Base Agent")
    parser.add_argument("goal", type=str, help="Запит або мета для агента")
    parser.add_argument("--vault", type=str, default=None, help="Шлях до сховища Obsidian")
    parser.add_argument("--max-steps", type=int, default=6, help="Ліміт кроків циклу")
    args = parser.parse_args()

    env = KnowledgeEnvironment(vault_path=args.vault)
    state = run_agent_loop(goal=args.goal, env=env, max_steps=args.max_steps)

    print("\n" + "=" * 60)
    print("ФІНАЛЬНА ВІДПОВІДЬ АГЕНТА:")
    print("=" * 60)
    print(state.final_answer)
    print("=" * 60)
    print(f"Зупинка: {state.stop_reason} | Кроків: {state.step} | LLM викликів: {state.llm_calls}")

if __name__ == "__main__":
    main()
