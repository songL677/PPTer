from __future__ import annotations

from pathlib import Path

from parsers.base import DocumentPage, ParsedDocument, ParserError


def parse_pdf(file_path: str | Path, file_name: str | None = None) -> ParsedDocument:
    try:
        import fitz
    except ImportError as exc:
        raise ParserError("缺少 PyMuPDF 依赖，请先运行：pip install -r requirements.txt") from exc

    path = Path(file_path)
    display_name = file_name or path.name

    try:
        document = fitz.open(str(path))
    except Exception as exc:
        raise ParserError(f"PDF 打开失败：{exc}") from exc

    pages: list[DocumentPage] = []
    warnings: list[str] = []

    try:
        page_count = document.page_count
        for index, page in enumerate(document, start=1):
            try:
                text = page.get_text("text").strip()
            except Exception as exc:
                text = ""
                warnings.append(f"第 {index} 页文字提取失败：{exc}")

            pages.append(
                DocumentPage(
                    number=index,
                    text=text,
                    title=f"第 {index} 页",
                    source_type="page",
                )
            )
    finally:
        document.close()

    if not pages:
        raise ParserError("PDF 没有可读取的页面。")

    if not any(page.text.strip() for page in pages):
        raise ParserError("PDF 未提取到可用文字，可能是扫描版图片 PDF。")

    return ParsedDocument(
        file_name=display_name,
        file_type="PDF",
        page_count=page_count,
        status="解析完成",
        pages=pages,
        warnings=warnings,
    )
