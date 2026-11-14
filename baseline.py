"""Порівняння трьох систем: One-shot LLM, Наївний RAG та Агент з базою знань (Крок 12)."""
import os
import time
from dotenv import load_dotenv
from agent.environment import KnowledgeEnvironment
from agent.loop import run_agent_loop

def _call_gemini_retry(client, model, contents, max_retries=4):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=contents)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"[Gemini Retry] Спроба {attempt+1} не вдалася ({e}). Очікування 4с...")
            time.sleep(4)

def run_oneshot(query: str) -> dict:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    t0 = time.time()
    resp = _call_gemini_retry(
        client,
        model=model,
        contents=f"Ти експерт з платформи оренди нерухомості SmartLease. Дай точну відповідь на запитання: {query}",
    )
    dt = time.time() - t0
    return {"answer": resp.text.strip(), "time": dt, "llm_calls": 1}

def run_naive_rag(query: str, env: KnowledgeEnvironment) -> dict:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    t0 = time.time()
    context = env.search_knowledge(query)
    prompt = (
        f"Ти експерт з платформи SmartLease. Відповідай на запитання на основі наведеного контексту.\n\n"
        f"КОНТЕКСТ:\n{context}\n\n"
        f"ЗАПИТАННЯ: {query}\n\n"
        "Якщо в контексті немає інформації — напиши, що сутність або інформація відсутня."
    )
    resp = _call_gemini_retry(
        client,
        model=model,
        contents=prompt,
    )
    dt = time.time() - t0
    return {"answer": resp.text.strip(), "time": dt, "llm_calls": 1, "context": context}

def run_agent(query: str, env: KnowledgeEnvironment) -> dict:
    t0 = time.time()
    state = run_agent_loop(goal=query, env=env)
    dt = time.time() - t0
    return {
        "answer": state.final_answer,
        "time": dt,
        "llm_calls": state.llm_calls,
        "steps": state.step,
        "stop_reason": state.stop_reason,
    }
