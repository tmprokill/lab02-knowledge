"""Модуль інкрементної індексації сховища знань."""
import hashlib
import json
import os
from pathlib import Path
from kb.vault import ObsidianVault
from kb.chunker import MarkdownChunker
from kb.embedder import KnowledgeEmbedder
from kb.store import KnowledgeStore

class KnowledgeIndexer:
    """Інкрементний індексатор сховища (Крок 7)."""

    def __init__(self, vault: ObsidianVault, store: KnowledgeStore, embedder: KnowledgeEmbedder):
        self.vault = vault
        self.store = store
        self.embedder = embedder
        self.state_file = self.store.persist_dir / ".index_state.json"
        self.state = self._load_state()

    def _load_state(self) -> dict[str, str]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def _hash_file(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def run(self) -> dict[str, int]:
        """Виконує інкрементне індексування.
        Повертає статистику: {added: N, updated: N, deleted: N, untouched: N}.
        """
        notes = self.vault.list_notes()
        current_paths = {str(p.relative_to(self.vault.vault_path)).replace("\\", "/"): p for p in notes}

        stats = {"added": 0, "updated": 0, "deleted": 0, "untouched": 0}
        chunker = MarkdownChunker()

        # 1. Обробка видалених нотаток
        for saved_rel_path in list(self.state.keys()):
            if saved_rel_path not in current_paths:
                print(f"[Indexer] Видалено файл: {saved_rel_path}")
                self.store.delete_by_path(saved_rel_path)
                del self.state[saved_rel_path]
                stats["deleted"] += 1

        # 2. Обробка доданих або модифікованих нотаток
        for rel_path, full_path in current_paths.items():
            current_hash = self._hash_file(full_path)
            prev_hash = self.state.get(rel_path)

            if prev_hash is None:
                # Новий файл
                note = self.vault.read_note(rel_path)
                chunks = chunker.chunk_note(note)
                texts = [c.text for c in chunks]
                embeddings = self.embedder.embed(texts, task_type="retrieval_document")
                self.store.add_chunks(chunks, embeddings)
                self.state[rel_path] = current_hash
                stats["added"] += 1
                print(f"[Indexer] Додано: {rel_path} ({len(chunks)} фрагментів)")

            elif prev_hash != current_hash:
                # Змінений файл
                self.store.delete_by_path(rel_path)
                note = self.vault.read_note(rel_path)
                chunks = chunker.chunk_note(note)
                texts = [c.text for c in chunks]
                embeddings = self.embedder.embed(texts, task_type="retrieval_document")
                self.store.add_chunks(chunks, embeddings)
                self.state[rel_path] = current_hash
                stats["updated"] += 1
                print(f"[Indexer] Оновлено: {rel_path} ({len(chunks)} фрагментів)")

            else:
                stats["untouched"] += 1

        self._save_state()
        print(f"[Indexer Підсумок] Додано: {stats['added']}, Оновлено: {stats['updated']}, Видалено: {stats['deleted']}, Без змін: {stats['untouched']}")
        return stats

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from dotenv import load_dotenv
    load_dotenv()

    vault_dir = os.getenv("KB_VAULT_PATH", "/mnt/c/Users/Alex/Documents/kb-vault")
    vault = ObsidianVault(vault_dir)
    store = KnowledgeStore()
    embedder = KnowledgeEmbedder()

    indexer = KnowledgeIndexer(vault, store, embedder)
    indexer.run()
