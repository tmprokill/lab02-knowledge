"""Перевірка обґрунтованості: чи кожне посилання [[...]] у відповіді
веде на джерело, яке агент справді отримав у спостереженнях (Лістинг 1.25 МВ).

Запуск:
    uv run python -m eval.citations traces/trace_....json
"""
import json
import re
import sys

CITATION = re.compile(r"\[\[([^\]]+)\]\]")
SOURCE = re.compile(r'(?:source|reference)="\[\[([^\]]+)\]\]"')

def check_citations(answer: str, observations: list[str]) -> dict:
    cited = CITATION.findall(answer or "")
    sources = {s.strip() for obs in observations for s in SOURCE.findall(obs or "")}
    # Також шукаємо будь-які внутрішні посилання з текстів спостережень
    for obs in observations:
        for m in CITATION.findall(obs or ""):
            sources.add(m.strip())

    titles = {s.split("#")[0].strip().lower() for s in sources}
    valid = []
    for c in cited:
        c_clean = c.strip()
        c_title = c_clean.split("#")[0].strip().lower()
        if c_clean in sources or c_title in titles or any(c_title in s.lower() for s in sources) or any(s in c_title for s in titles):
            valid.append(c)

    invalid = sorted(set(cited) - set(valid))
    return {
        "cited": len(cited),
        "valid": len(valid),
        "invalid": invalid,
        "grounded": bool(cited) and len(invalid) == 0,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:

        print("Usage: python -m eval.citations <trace_file.json>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    trace = data.get("trace", [])
    observations = [r.get("observation", "") for r in trace if r.get("observation")]
    answer = data.get("final_answer", "")

    result = check_citations(answer, observations)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
