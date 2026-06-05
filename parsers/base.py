from dataclasses import dataclass, field


class ParserError(Exception):
    """Raised when a courseware file cannot be parsed into usable text."""


@dataclass
class DocumentPage:
    number: int
    text: str
    title: str = ""
    source_type: str = "page"

    @property
    def source_label(self) -> str:
        label = "页" if self.source_type == "page" else "张幻灯片"
        return f"第 {self.number} {label}"


@dataclass
class ParsedDocument:
    file_name: str
    file_type: str
    page_count: int
    status: str
    pages: list[DocumentPage] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def text_page_count(self) -> int:
        return sum(1 for page in self.pages if page.text.strip())
