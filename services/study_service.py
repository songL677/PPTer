from __future__ import annotations

from pathlib import Path

from ai.api_client import OpenAICompatibleClient
from ai.ollama_client import OllamaClient
from ai.prompts import CHUNK_PROMPT_TEMPLATE, FINAL_PROMPT_TEMPLATE
from parsers.base import ParsedDocument, ParserError
from parsers.pdf_parser import parse_pdf
from parsers.pptx_parser import parse_pptx
from storage.db import save_history


MAX_FILE_SIZE_MB = 80


class StudyServiceError(Exception):
    """User-facing error for the study assistant workflow."""


def validate_file_size(file_size_bytes: int) -> None:
    size_mb = file_size_bytes / 1024 / 1024
    if size_mb > MAX_FILE_SIZE_MB:
        raise StudyServiceError(
            f"文件过大：{size_mb:.1f} MB。当前 MVP 建议上传 {MAX_FILE_SIZE_MB} MB 以内的课件。"
        )


def parse_courseware(file_path: str | Path, file_name: str) -> ParsedDocument:
    suffix = Path(file_name).suffix.lower()
    try:
        if suffix == ".pdf":
            return parse_pdf(file_path, file_name)
        if suffix == ".pptx":
            return parse_pptx(file_path, file_name)
    except ParserError as exc:
        raise StudyServiceError(str(exc)) from exc

    raise StudyServiceError("暂时只支持 PDF 和 PPTX 文件。")


def _page_to_text(page) -> str:
    title = f"\n标题：{page.title}" if page.title else ""
    body = page.text.strip() or "(本页未提取到正文文字)"
    return f"[{page.source_label}]{title}\n{body}".strip()


def build_chunks(document: ParsedDocument, max_chars: int = 6000) -> list[str]:
    chunks: list[str] = []
    current_parts: list[str] = []
    current_size = 0

    for page in document.pages:
        page_text = _page_to_text(page)
        if not page_text.strip():
            continue

        if current_parts and current_size + len(page_text) > max_chars:
            chunks.append("\n\n".join(current_parts))
            current_parts = []
            current_size = 0

        current_parts.append(page_text)
        current_size += len(page_text)

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    if not chunks:
        raise StudyServiceError("课件没有可用于生成的文字内容。")
    return chunks


def generate_study_material(
    document: ParsedDocument,
    model_name: str = "qwen2.5:7b",
    ollama_base_url: str = "http://localhost:11434",
    provider: str = "ollama",
    api_base_url: str = "",
    api_key: str = "",
    chunk_chars: int = 6000,
    progress_callback=None,
) -> str:
    if provider == "custom_api":
        client = OpenAICompatibleClient(base_url=api_base_url, api_key=api_key)
        history_model_name = f"自定义 API / {model_name}"
    else:
        client = OllamaClient(base_url=ollama_base_url)
        history_model_name = f"Ollama / {model_name}"

    chunks = build_chunks(document, max_chars=chunk_chars)

    chunk_summaries: list[str] = []
    for index, chunk_text in enumerate(chunks, start=1):
        if progress_callback:
            progress_callback("chunk", index, len(chunks))
        prompt = CHUNK_PROMPT_TEMPLATE.format(chunk_text=chunk_text)
        summary = client.generate(model=model_name, prompt=prompt)
        chunk_summaries.append(f"## 分块 {index}\n\n{summary}")

    if progress_callback:
        progress_callback("final", len(chunks), len(chunks))

    if len(chunk_summaries) == 1:
        final_prompt = FINAL_PROMPT_TEMPLATE.format(chunk_summaries=chunk_summaries[0])
    else:
        final_prompt = FINAL_PROMPT_TEMPLATE.format(
            chunk_summaries="\n\n".join(chunk_summaries)
        )

    result = client.generate(model=model_name, prompt=final_prompt)
    save_history(document.file_name, history_model_name, result)
    return result
