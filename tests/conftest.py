import pytest
from pathlib import Path

@pytest.fixture
def test_vault_path(tmp_path):
    # Створюємо тимчасовий волт для тестів
    vault = tmp_path / "kb-vault"
    vault.mkdir()
    (vault / "Architecture").mkdir()
    (vault / "Inbox").mkdir()

    note1 = vault / "Architecture" / "test_note.md"
    note1.write_text(
        "---\ntags: [test, core]\nsource: Test Spec\nupdated: 2026-11-15\n---\n\n"
        "# Тестова Нотатка\n\nВступний опис.\n\n"
        "## Розділ Перший\nВміст першого розділу з [[link_note]].\n\n"
        "## Розділ Другий\nВміст другого розділу.\n",
        encoding="utf-8"
    )

    note2 = vault / "Architecture" / "link_note.md"
    note2.write_text(
        "---\ntags: [test]\nsource: Test Spec 2\nupdated: 2026-11-15\n---\n\n"
        "# Зв'язана Нотатка\n\nВміст зв'язаної нотатки.\n",
        encoding="utf-8"
    )

    return vault
