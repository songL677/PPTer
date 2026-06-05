import re
from datetime import datetime
from pathlib import Path


EXPORT_DIR = Path("generated_exports")


def _safe_name(value: str) -> str:
    stem = Path(value).stem or "study-notes"
    return re.sub(r"[^A-Za-z0-9\u4e00-\u9fff._-]+", "_", stem).strip("_")


def build_markdown(file_name: str, model_name: str, result_markdown: str) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"<!-- 原始文件：{file_name} -->\n"
        f"<!-- 模型：{model_name} -->\n"
        f"<!-- 导出时间：{generated_at} -->\n\n"
        f"{result_markdown.strip()}\n"
    )


def export_markdown(file_name: str, model_name: str, result_markdown: str) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = EXPORT_DIR / f"{_safe_name(file_name)}_{timestamp}.md"
    output_path.write_text(
        build_markdown(file_name, model_name, result_markdown),
        encoding="utf-8",
    )
    return output_path
