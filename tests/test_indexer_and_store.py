import pytest
from kb.vault import ObsidianVault
from kb.store import KnowledgeStore
from kb.embedder import KnowledgeEmbedder
from kb.indexer import KnowledgeIndexer

def test_incremental_indexer(test_vault_path, tmp_path):
    store = KnowledgeStore(persist_dir=tmp_path / "chroma_test")
    embedder = KnowledgeEmbedder(api_key=None) # will use deterministic fallback vector
    vault = ObsidianVault(test_vault_path)

    indexer = KnowledgeIndexer(vault, store, embedder)

    # 1. Первинна індексація
    stats1 = indexer.run()
    assert stats1["added"] == 2
    assert stats1["untouched"] == 0

    # 2. Повторна індексація без змін
    stats2 = indexer.run()
    assert stats2["added"] == 0
    assert stats2["untouched"] == 2

    # 3. Додавання нової нотатки
    new_note = test_vault_path / "Inbox" / "new_note.md"
    new_note.write_text("# Нова Нотатка\n\nВміст нової нотатки.\n", encoding="utf-8")
    stats3 = indexer.run()
    assert stats3["added"] == 1
    assert stats3["untouched"] == 2

    # 4. Видалення нотатки
    new_note.unlink()
    stats4 = indexer.run()
    assert stats4["deleted"] == 1
    assert stats4["untouched"] == 2

def test_store_tag_filter_and_distance(test_vault_path, tmp_path):
    store = KnowledgeStore(persist_dir=tmp_path / "chroma_filter_test")
    embedder = KnowledgeEmbedder(api_key=None)
    vault = ObsidianVault(test_vault_path)
    indexer = KnowledgeIndexer(vault, store, embedder)
    indexer.run()

    # Пошук за вектором
    q_vec = embedder.embed(["Тестова нотатка"], task_type="retrieval_query")[0]
    res_all = store.query(q_vec, n_results=5)
    assert len(res_all) > 0

    # Пошук з фільтром за тегом
    res_filtered = store.query(q_vec, n_results=5, tag_filter="core")
    assert len(res_filtered) > 0
    for r in res_filtered:
        assert "core" in r["metadata"]["tags"]
