"""Модуль семантичного розбиття нотаток на фрагменти."""
from dataclasses import dataclass
import re
from kb.vault import VaultNote

@dataclass
class DocumentChunk:
    """Фрагмент нотатки для векторного індексування."""
    chunk_id: str
    rel_path: str
    note_title: str
    section_heading: str
    reference: str  # [[NoteTitle#Section]]
    text: str
    tags: list[str]
    source: str

class MarkdownChunker:
    """Розбиває Markdown-нотатки на семантичні фрагменти за заголовками ##."""

    def __init__(self, chunk_chars: int = 700, overlap: int = 80):
        self.chunk_chars = chunk_chars
        self.overlap = overlap

    def chunk_note(self, note: VaultNote) -> list[DocumentChunk]:
        """Розбиває нотатку на фрагменти за заголовками ## або лімітом символів."""
        chunks: list[DocumentChunk] = []

        # Розбиття за заголовками другого рівня (## )
        sections = re.split(r"(?m)^##\s+", note.content)

        # Перша частина — вступ (до першого ##)
        intro_text = sections[0].strip()
        if intro_text:
            chunks.append(DocumentChunk(
                chunk_id=f"{note.title}::intro",
                rel_path=note.rel_path,
                note_title=note.title,
                section_heading="Вступ",
                reference=f"[[{note.title}#Вступ]]",
                text=intro_text,
                tags=note.tags,
                source=note.source,
            ))

        # Наступні секції містять назву заголовка в першому рядку
        for idx, sec in enumerate(sections[1:], start=1):
            lines = sec.strip().split("\n")
            heading = lines[0].strip()
            body = "\n".join(lines[1:]).strip()

            full_text = f"## {heading}\n{body}" if body else f"## {heading}"

            # Якщо фрагмент довший за chunk_chars — розбиваємо з перекриттям
            if len(full_text) > self.chunk_chars:
                start = 0
                part = 1
                while start < len(full_text):
                    end = start + self.chunk_chars
                    sub_text = full_text[start:end]
                    chunk_id = f"{note.title}::{heading}::p{part}"
                    chunks.append(DocumentChunk(
                        chunk_id=chunk_id,
                        rel_path=note.rel_path,
                        note_title=note.title,
                        section_heading=heading,
                        reference=f"[[{note.title}#{heading}]]",
                        text=sub_text.strip(),
                        tags=note.tags,
                        source=note.source,
                    ))
                    start += (self.chunk_chars - self.overlap)
                    part += 1
            else:
                chunk_id = f"{note.title}::{heading}"
                chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    rel_path=note.rel_path,
                    note_title=note.title,
                    section_heading=heading,
                    reference=f"[[{note.title}#{heading}]]",
                    text=full_text,
                    tags=note.tags,
                    source=note.source,
                ))

        return chunks
