from kb.vault import ObsidianVault
from kb.chunker import MarkdownChunker

def test_chunking_by_headings(test_vault_path):
    vault = ObsidianVault(test_vault_path)
    note = vault.read_note("Architecture/test_note.md")

    chunker = MarkdownChunker(chunk_chars=500)
    chunks = chunker.chunk_note(note)

    # Має бути intro + Розділ Перший + Розділ Другий
    assert len(chunks) == 3
    headings = [c.section_heading for c in chunks]
    assert "Вступ" in headings
    assert "Розділ Перший" in headings
    assert "Розділ Другий" in headings
    assert chunks[1].reference == "[[Тестова Нотатка#Розділ Перший]]"
