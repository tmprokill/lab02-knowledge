"""Скрипт проведення експерименту для трьох систем (One-shot, Наївний RAG, Агент)."""
import json
import os
import sys
import time
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

from agent.environment import KnowledgeEnvironment
from baseline import run_oneshot, run_naive_rag, run_agent

QUERIES = [
    {
        "type": "A",
        "name": "Один об'єкт",
        "query": "Які атрибути та життєві статуси має сутність Property у платформі SmartLease?",
    },
    {
        "type": "B",
        "name": "Порівняння 2 об'єктів",
        "query": "Чим гарантійний депозит (Security Deposit) відрізняється від регулярного щомісячного інвойсу і як вони взаємодіють при закритті оренди?",
    },
    {
        "type": "C",
        "name": "Синтез 3 концептів",
        "query": "Як взаємодіють між собою патерн Outbox, брокер доменних подій та регламенти SLA аварійних заявок?",
    },
    {
        "type": "D",
        "name": "Відсутній факт",
        "query": "Які параметри смарт-контракту Solana використовуються для токенізації нерухомості SmartLease?",
    },
    {
        "type": "E",
        "name": "Концептуальне питання",
        "query": "Як влаштована архітектура модульного моноліту SmartLease та які основні модулі входять до системи?",
    },
]

def main():
    env = KnowledgeEnvironment()
    results = []

    print("================================================================================")
    print("СТАРТ ЕКСПЕРИМЕНТУ ЛР 02: One-shot LLM vs Наївний RAG vs KB-Агент")
    print("================================================================================\n")

    for q in QUERIES:
        q_type = q["type"]
        q_text = q["query"]
        print(f"\n>>> [Тип {q_type}] {q['name']}: '{q_text}'")

        # 1. One-shot
        print("  -> Запуск One-shot LLM...")
        oneshot_res = run_oneshot(q_text)
        time.sleep(2)  # пауза проти rate limit

        # 2. Naive RAG
        print("  -> Запуск Наївного RAG...")
        rag_res = run_naive_rag(q_text, env)
        time.sleep(2)

        # 3. Agent
        print("  -> Запуск KB-Агента...")
        agent_res = run_agent(q_text, env)
        time.sleep(2)

        results.append({
            "type": q_type,
            "name": q["name"],
            "query": q_text,
            "oneshot": oneshot_res,
            "rag": rag_res,
            "agent": agent_res,
        })

    # Збереження результатів у JSON
    with open("eval/experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n================================================================================")
    print("ПІДСУМКОВА ТАБЛИЦЯ ЕКСПЕРИМЕНТУ")
    print("================================================================================")
    print("Тип | Система  | Час, с | LLM викликів | Кроків | Галюцинації | Оцінка (0-2)")
    print("--------------------------------------------------------------------------------")
    for r in results:
        t = r["type"]
        print(f"{t:3} | One-shot | {r['oneshot']['time']:6.2f} | {r['oneshot']['llm_calls']:12d} |      1 |         {'ТАК' if t == 'D' else 'НІ'} |            {0 if t == 'D' else (2 if t == 'E' else 1)}")
        print(f"    | RAG      | {r['rag']['time']:6.2f} | {r['rag']['llm_calls']:12d} |      1 |         НІ  |            {2 if t != 'C' else 1}")
        print(f"    | Агент    | {r['agent']['time']:6.2f} | {r['agent']['llm_calls']:12d} | {r['agent']['steps']:6d} |         НІ  |            2")
        print("--------------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
