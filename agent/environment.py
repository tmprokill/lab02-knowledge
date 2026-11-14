"""Середовище агента: пошук у базі знань та безпечне читання/запис нотаток."""
import os
from pathlib import Path
from kb.vault import ObsidianVault
from kb.store import KnowledgeStore
from kb.embedder import KnowledgeEmbedder

class KnowledgeEnvironment:
    """Дії над сховищем знань та векторним індексом Chroma."""

    def __init__(self, vault_path: str | Path | None = None, max_distance: float = 0.45):
        v_str = str(vault_path or os.getenv("KB_VAULT_PATH", "C:/Users/Alex/Documents/kb-vault")).strip()
        if os.name != "nt" and len(v_str) >= 2 and v_str[1] == ":":
            drive = v_str[0].lower()
            rest = v_str[2:].replace("\\", "/").lstrip("/")
            v_str = f"/mnt/{drive}/{rest}"
        self.vault_path = Path(v_str).resolve()
        self.vault = ObsidianVault(self.vault_path)

        self.store = KnowledgeStore()
        self.embedder = KnowledgeEmbedder()
        self.max_distance = float(os.getenv("KB_MAX_DISTANCE", str(max_distance)))

    def search_knowledge(self, query: str, tag: str | None = None) -> str:
        """Семантичний пошук у базі знань.
        Повертає фрагменти у тегах <fragment reference="[[Note#Section]]"> або маркер NOT_FOUND.
        """
        q_vec = self.embedder.embed([query], task_type="retrieval_query")[0]
        results = self.store.query(q_vec, n_results=3, tag_filter=tag)

        valid_results = [r for r in results if r["distance"] <= self.max_distance]
        if not valid_results:
            return "NOT_FOUND: Жодного релевантного фрагмента в базі знань нижче порогу відстані не знайдено."

        output = []
        for r in valid_results:
            ref = r["metadata"].get("reference", "[[Документ]]")
            text = r["text"].strip()
            dist = r["distance"]
            output.append(f'<fragment reference="{ref}" distance="{dist:.3f}">\n{text}\n</fragment>')
        return "\n\n".join(output)

    def read_note(self, rel_path: str) -> str:
        """Повертає повний вміст нотатки із захистом від path traversal."""
        try:
            note = self.vault.read_note(rel_path)
            return (
                f"--- ЗМІСТ НОТАТКИ {note.title} ({note.rel_path}) ---\n"
                f"Джерело: {note.source} | Оновлено: {note.updated}\n"
                f"Теги: {', '.join(note.tags)}\n\n"
                f"{note.content}"
            )
        except Exception as e:
            return f"ERROR_READ_NOTE: {e}"

    def write_note(self, title: str, content: str, confirm: bool = False) -> str:
        """Human-in-the-loop дія запису (Крок 17).
        Створює нотатку виключно в папці Inbox/ і лише після підтвердження користувачем.
        """
        clean_title = Path(title).stem
        inbox_dir = self.vault_path / "Inbox"
        inbox_dir.mkdir(parents=True, exist_ok=True)
        target_path = inbox_dir / f"{clean_title}.md"

        if not confirm:
            return (
                f"CONFIRMATION_REQUIRED: Дія write_note створює файл '{target_path.name}' у папці Inbox/. "
                "Потрібне явне підтвердження користувачем (Human-in-the-loop)."
            )

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(f"---\ntags: [smartlease, inbox, generated]\nsource: Agent write_note\nupdated: 2026-11-15\n---\n\n# {clean_title}\n\n{content.strip()}\n")

        return f"SUCCESS: Нотатку успішно записано у папку Inbox: [[Inbox/{clean_title}]]"
