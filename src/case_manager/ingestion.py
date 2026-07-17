import re
from pathlib import Path

import fitz

ALLOWED = {".pdf", ".txt", ".md"}


class IngestionError(ValueError):
    pass


def extract_text(filename: str, content: bytes, max_bytes: int) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED:
        raise IngestionError("Formato não suportado. Use PDF, TXT ou Markdown.")
    if not content:
        raise IngestionError("Arquivo vazio.")
    if len(content) > max_bytes:
        raise IngestionError("Arquivo excede o limite configurado.")
    if suffix != ".pdf":
        return content.decode("utf-8", errors="replace").strip()
    if not content.startswith(b"%PDF"):
        raise IngestionError("Assinatura PDF inválida.")
    try:
        pdf = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise IngestionError("PDF inválido ou corrompido.") from exc
    pages = [f"[Página {number}]\n{page.get_text().strip()}" for number, page in enumerate(pdf, 1)]
    text = "\n\n".join(pages)
    if len(re.sub(r"\[Página \d+\]", "", text).strip()) < 20:
        raise IngestionError("PDF sem texto suficiente; encaminhe ao pipeline OCR.")
    return text
