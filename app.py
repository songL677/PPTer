import tempfile
from pathlib import Path

import streamlit as st

from exports.markdown_exporter import build_markdown, export_markdown
from services.study_service import (
    MAX_FILE_SIZE_MB,
    StudyServiceError,
    generate_study_material,
    parse_courseware,
    validate_file_size,
)
from storage.db import get_history, init_db, list_history


st.set_page_config(
    page_title="PPTer",
    page_icon="📚",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; max-width: 1180px; }
    .small-muted { color: #6b7280; font-size: 0.92rem; }
    .status-box {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        background: #fafafa;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _safe_download_name(file_name: str) -> str:
    return f"{Path(file_name).stem or 'study_notes'}_notes.md"


def _parse_uploaded_file(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    validate_file_size(len(file_bytes))

    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = Path(tmp_file.name)

    try:
        return parse_courseware(tmp_path, uploaded_file.name)
    finally:
        tmp_path.unlink(missing_ok=True)


def _model_from_sidebar():
    st.sidebar.header("模型设置")
    provider_label = st.sidebar.radio(
        "AI 后端",
        ["本地 Ollama", "自定义 API"],
        horizontal=True,
    )

    if provider_label == "自定义 API":
        provider = "custom_api"
        api_base_url = st.sidebar.text_input(
            "API Base URL",
            value="https://api.openai.com/v1",
            help="支持 OpenAI Chat Completions 兼容接口，例如 OpenAI、DeepSeek、硅基流动或本地兼容服务。",
        ).strip()
        api_key = st.sidebar.text_input(
            "API Key",
            value="",
            type="password",
            help="只在当前页面会话中使用，不会写入历史记录。",
        )
        model_name = st.sidebar.text_input(
            "模型名称",
            value="gpt-4.1-mini",
            help="填写你的 API 服务支持的模型名。",
        ).strip()
        ollama_url = "http://localhost:11434"
    else:
        provider = "ollama"
        model_choice = st.sidebar.selectbox(
            "Ollama 模型",
            ["qwen2.5:7b", "llama3.1:8b", "自定义"],
            index=0,
        )
        if model_choice == "自定义":
            model_name = st.sidebar.text_input("模型名称", value="qwen2.5:7b").strip()
        else:
            model_name = model_choice

        ollama_url = st.sidebar.text_input(
            "Ollama 地址",
            value="http://localhost:11434",
            help="默认本地 Ollama 服务地址。",
        ).strip()
        api_base_url = ""
        api_key = ""

    chunk_chars = st.sidebar.slider(
        "每个分块最大字符数",
        min_value=2500,
        max_value=12000,
        value=6000,
        step=500,
        help="课件很长时调小可以减少模型上下文压力，但会增加调用次数。",
    )
    return {
        "provider": provider,
        "provider_label": provider_label,
        "model_name": model_name,
        "ollama_url": ollama_url,
        "api_base_url": api_base_url,
        "api_key": api_key,
        "chunk_chars": chunk_chars,
    }


init_db()

if "parsed_document" not in st.session_state:
    st.session_state.parsed_document = None
if "uploaded_key" not in st.session_state:
    st.session_state.uploaded_key = None
if "result_markdown" not in st.session_state:
    st.session_state.result_markdown = ""
if "result_file_name" not in st.session_state:
    st.session_state.result_file_name = ""
if "result_model_name" not in st.session_state:
    st.session_state.result_model_name = ""

model_settings = _model_from_sidebar()
model_name = model_settings["model_name"]

st.title("PPTer")
st.caption("本地运行的课程 PDF / PPTX 复习材料生成原型。")

upload_col, parse_col = st.columns([1.1, 0.9], gap="large")

with upload_col:
    st.subheader("上传课件")
    uploaded_file = st.file_uploader(
        "选择 PDF 或 PPTX 文件",
        type=["pdf", "pptx"],
        help=f"当前 MVP 建议文件大小不超过 {MAX_FILE_SIZE_MB} MB。",
    )

    if uploaded_file:
        uploaded_key = f"{uploaded_file.name}-{uploaded_file.size}"
        if uploaded_key != st.session_state.uploaded_key:
            try:
                with st.spinner("正在解析课件内容..."):
                    st.session_state.parsed_document = _parse_uploaded_file(uploaded_file)
                st.session_state.uploaded_key = uploaded_key
                st.session_state.result_markdown = ""
            except StudyServiceError as exc:
                st.session_state.parsed_document = None
                st.session_state.uploaded_key = uploaded_key
                st.error(str(exc))

with parse_col:
    st.subheader("解析状态")
    document = st.session_state.parsed_document
    if document:
        st.markdown('<div class="status-box">', unsafe_allow_html=True)
        metric_a, metric_b, metric_c = st.columns(3)
        metric_a.metric("文件", document.file_type)
        metric_b.metric("页数/幻灯片", document.page_count)
        metric_c.metric("含文字页", document.text_page_count)
        st.write(f"**文件名：** {document.file_name}")
        st.success(document.status)
        st.markdown("</div>", unsafe_allow_html=True)

        if document.warnings:
            with st.expander("解析提示"):
                for warning in document.warnings:
                    st.warning(warning)
    else:
        st.info("上传课件后会显示文件名、页数/幻灯片数量和解析状态。")

st.divider()

result_tab, history_tab = st.tabs(["生成结果", "历史记录"])

with result_tab:
    document = st.session_state.parsed_document
    generate_disabled = document is None or not model_name

    action_col, hint_col = st.columns([0.25, 0.75])
    with action_col:
        generate_clicked = st.button(
            "生成复习材料",
            type="primary",
            disabled=generate_disabled,
            use_container_width=True,
        )
    with hint_col:
        if model_settings["provider"] == "custom_api":
            hint = "生成会调用你填写的 OpenAI 兼容 API。API Key 只用于本次页面会话。"
        else:
            hint = "生成会调用本机 Ollama。第一次运行模型可能较慢，请保持 Ollama 已启动。"
        st.markdown(f'<p class="small-muted">{hint}</p>', unsafe_allow_html=True)

    if generate_clicked and document:
        progress_bar = st.progress(0)
        progress_text = st.empty()

        def update_progress(stage: str, current: int, total: int) -> None:
            if stage == "chunk":
                progress_text.write(f"正在处理分块 {current}/{total} ...")
                progress_bar.progress(min(current / max(total + 1, 1), 0.9))
            else:
                progress_text.write("正在整合最终复习材料 ...")
                progress_bar.progress(0.95)

        try:
            with st.spinner("AI 正在生成，请稍候..."):
                result = generate_study_material(
                    document=document,
                    model_name=model_name,
                    ollama_base_url=model_settings["ollama_url"],
                    provider=model_settings["provider"],
                    api_base_url=model_settings["api_base_url"],
                    api_key=model_settings["api_key"],
                    chunk_chars=model_settings["chunk_chars"],
                    progress_callback=update_progress,
                )
            progress_bar.progress(1.0)
            progress_text.write("生成完成。")
            st.session_state.result_markdown = result
            st.session_state.result_file_name = document.file_name
            st.session_state.result_model_name = (
                f"{model_settings['provider_label']} / {model_name}"
            )
            st.success("复习材料已生成，并已保存到本地历史记录。")
        except Exception as exc:
            st.error(str(exc))

    if st.session_state.result_markdown:
        file_name = st.session_state.result_file_name
        current_model = st.session_state.result_model_name
        markdown_content = build_markdown(
            file_name=file_name,
            model_name=current_model,
            result_markdown=st.session_state.result_markdown,
        )

        export_col, download_col = st.columns([0.24, 0.76])
        with export_col:
            if st.button("保存为 Markdown", use_container_width=True):
                output_path = export_markdown(
                    file_name=file_name,
                    model_name=current_model,
                    result_markdown=st.session_state.result_markdown,
                )
                st.success(f"已保存：{output_path}")
        with download_col:
            st.download_button(
                "下载 Markdown",
                data=markdown_content,
                file_name=_safe_download_name(file_name),
                mime="text/markdown",
                use_container_width=True,
            )

        st.markdown(st.session_state.result_markdown)
        with st.expander("复制用 Markdown 原文"):
            st.text_area(
                "Markdown",
                value=markdown_content,
                height=320,
                label_visibility="collapsed",
            )
    else:
        st.info("上传课件并点击“生成复习材料”后，结果会显示在这里。")

with history_tab:
    history_rows = list_history(limit=30)
    if not history_rows:
        st.info("暂无历史记录。")
    else:
        labels = [
            f"#{row['id']} | {row['generated_at']} | {row['file_name']} | {row['model_name']}"
            for row in history_rows
        ]
        selected_label = st.selectbox("选择历史记录", labels)
        selected_id = int(selected_label.split("|", 1)[0].replace("#", "").strip())
        record = get_history(selected_id)

        if record:
            st.write(f"**文件名：** {record['file_name']}")
            st.write(f"**生成时间：** {record['generated_at']}")
            st.write(f"**模型：** {record['model_name']}")
            history_markdown = build_markdown(
                file_name=record["file_name"],
                model_name=record["model_name"],
                result_markdown=record["result_markdown"],
            )
            st.download_button(
                "下载这条历史记录",
                data=history_markdown,
                file_name=_safe_download_name(record["file_name"]),
                mime="text/markdown",
            )
            st.markdown(record["result_markdown"])
