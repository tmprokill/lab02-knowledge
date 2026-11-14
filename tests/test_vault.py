import pytest
from kb.vault import ObsidianVault

def test_list_notes(test_vault_path):
    vault = ObsidianVault(test_vault_path)
    notes = vault.list_notes()
    assert len(notes) == 2

def test_read_note_properties_and_links(test_vault_path):
    vault = ObsidianVault(test_vault_path)
    note = vault.read_note("Architecture/test_note.md")
    assert note.title == "Тестова Нотатка"
    assert "test" in note.tags
    assert "core" in note.tags
    assert "link_note" in note.wiki_links

def test_path_traversal_protection(test_vault_path):
    vault = ObsidianVault(test_vault_path)
    with pytest.raises(PermissionError):
        vault.read_note("../../etc/passwd")

def test_nonexistent_note_error(test_vault_path):
    vault = ObsidianVault(test_vault_path)
    with pytest.raises(FileNotFoundError):
        vault.read_note("Architecture/ghost.md")
