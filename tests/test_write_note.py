import pytest
from agent.environment import KnowledgeEnvironment

def test_write_note_requires_confirmation(test_vault_path):
    env = KnowledgeEnvironment(vault_path=test_vault_path)
    res = env.write_note("test_title", "test_content", confirm=False)
    assert "CONFIRMATION_REQUIRED" in res
    assert not (test_vault_path / "Inbox" / "test_title.md").exists()

def test_write_note_confirmed_writes_only_to_inbox(test_vault_path):
    env = KnowledgeEnvironment(vault_path=test_vault_path)
    res = env.write_note("approved_note", "Вміст підтвердженої нотатки", confirm=True)
    assert "SUCCESS" in res
    target_file = test_vault_path / "Inbox" / "approved_note.md"
    assert target_file.exists()
    content = target_file.read_text(encoding="utf-8")
    assert "approved_note" in content
    assert "Вміст підтвердженої нотатки" in content
