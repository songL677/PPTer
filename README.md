# PPTer

PPTer 是一个本地运行的课件学习助手 MVP。用户可以上传课程 PDF 或 PPTX 课件，软件会解析文字内容，并调用本机 Ollama 模型生成复习材料。

项目定位是“可跑通功能闭环的桌面原型”：不需要服务器、不需要用户登录，适合学生把课程资料快速整理为考前复习笔记、可能考点和练习题。

## 功能

- 上传 PDF / PPTX 课件
- 显示文件名、页数或幻灯片数量、解析状态
- PDF 使用 PyMuPDF 提取文字
- PPTX 使用 python-pptx 提取标题和正文
- 按页或幻灯片保留来源编号
- 调用本地 Ollama 模型生成中文复习材料
- 支持分块处理，避免一次性输入过长
- 生成课程章节大纲、核心知识点、重点难点、可能考点、练习题、答案解析
- 使用 SQLite 保存历史记录
- 支持导出 Markdown 文件
- 支持本地 Ollama 或自定义 OpenAI 兼容 API
- 支持打包为可双击运行的桌面应用

> 说明：当前 MVP 支持 `.pdf` 和 `.pptx`。旧版 `.ppt` 暂未支持，可先用 PowerPoint、Keynote 或 WPS 转成 `.pptx`。

## 工作流程

1. 上传课程 PDF 或 PPTX。
2. 程序按页或幻灯片提取文本，并保留来源编号。
3. 长课件会被自动分块，避免一次性输入过长。
4. AI 先对每个分块生成阶段性复习材料。
5. AI 再整合所有分块，输出完整 Markdown 复习笔记。
6. 生成结果会保存到 SQLite 历史记录，并可导出为 Markdown。

## 生成内容

生成结果默认包含：

- 课程章节大纲
- 核心知识点总结
- 重点、难点与易混点
- 可能考点预测，按重要程度标记
- 单选题、判断题、简答题
- 每道题的参考答案和简短解析

> “可能考点”只基于课件内容生成，不代表真实考试预测。

## 项目结构

```text
.
├── app.py
├── ai/
│   ├── api_client.py
│   ├── ollama_client.py
│   └── prompts.py
├── parsers/
│   ├── base.py
│   ├── pdf_parser.py
│   └── pptx_parser.py
├── services/
│   └── study_service.py
├── storage/
│   └── db.py
├── exports/
│   └── markdown_exporter.py
├── desktop_app.py
├── packaging/
│   ├── build_macos_app.sh
│   └── build_windows_app.ps1
├── requirements.txt
├── requirements-build.txt
└── README.md
```

## 本地安装

建议使用 Python 3.9 或更高版本。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 安装和启动 Ollama

1. 安装 Ollama：访问 https://ollama.com 下载并安装。
2. 启动 Ollama：

```bash
ollama serve
```

如果使用 Ollama 桌面版，通常打开应用后本地服务会自动运行。

## 拉取模型

默认推荐：

```bash
ollama pull qwen2.5:7b
```

可选模型：

```bash
ollama pull llama3.1:8b
```

如果电脑内存较小，可以换用更小的模型；如果电脑性能较好，可以尝试更大的中文能力模型。

## 运行项目

```bash
streamlit run app.py
```

启动后浏览器会打开本地页面。上传 PDF 或 PPTX 后，点击“生成复习材料”即可。

## 使用自己的 API

页面左侧的“模型设置”支持两种 AI 后端：

1. 本地 Ollama：适合完全本地运行，不需要联网 API。
2. 自定义 API：适合接入你自己的 OpenAI 兼容接口。

自定义 API 需要填写：

- API Base URL，例如 `https://api.openai.com/v1`
- API Key
- 模型名称，例如 `gpt-4.1-mini`、`deepseek-chat`，或你的服务商提供的模型名

自定义 API 使用 OpenAI Chat Completions 兼容格式：

```text
POST /v1/chat/completions
```

API Key 只在当前页面会话中使用，不会保存进 SQLite 历史记录。

## 隐私与本地数据

- 上传的课件只在本机运行时解析，不会被保存到项目目录。
- 本地 Ollama 模式下，课件文本不会发送到外部 API。
- 自定义 API 模式下，课件文本会发送给你填写的 API 服务商。
- SQLite 历史记录只保存文件名、生成时间、模型名称和生成结果。
- API Key 不写入 SQLite，也不会写入导出的 Markdown。

## 本地桌面应用模式

开发阶段可以直接运行桌面入口：

```bash
python desktop_app.py
```

它会自动启动本地 Streamlit 服务，并打开一个桌面窗口。如果当前系统缺少桌面窗口依赖，会自动退回到浏览器打开。

## 打包为可下载应用

### macOS

```bash
source .venv/bin/activate
bash packaging/build_macos_app.sh
```

打包完成后应用位于：

```text
dist/PPTer.app
```

可以把这个 `.app` 压缩成 zip 后发给别人下载。

当前打包方式优先保证稳定：双击应用后会启动本地 GUI 服务，并在系统浏览器中打开界面。后续如果要做完全独立原生窗口，可以再加入 pywebview、Tauri 或 Electron 包装。

如果 macOS 提示应用来自未知开发者，可以在 Finder 中右键点击应用，选择“打开”。正式发布前建议做开发者签名和 notarization。

### Windows

在 PowerShell 中运行：

```powershell
.\.venv\Scripts\Activate.ps1
.\packaging\build_windows_app.ps1
```

打包完成后应用位于：

```text
dist/PPTer/PPTer.exe
```

注意：PyInstaller 通常需要在目标系统对应平台打包。也就是说，macOS 上打包 `.app`，Windows 上打包 `.exe`。

## 常见问题排查

### 1. 提示无法连接本地 Ollama

请确认 Ollama 已启动：

```bash
ollama serve
```

默认地址是：

```text
http://localhost:11434
```

### 2. 提示模型不可用或调用失败

请先拉取模型：

```bash
ollama pull qwen2.5:7b
```

或者在侧边栏填写你已经安装的模型名称。

### 2.1 自定义 API 调用失败

请检查：

- API Base URL 是否包含正确域名，通常以 `/v1` 结尾
- API Key 是否有效
- 模型名称是否是服务商支持的模型
- 当前电脑是否可以访问该 API 服务

### 3. PDF 没有提取到文字

这通常是扫描版 PDF，页面内容其实是图片。当前 MVP 暂未加入 OCR，可以先使用 OCR 工具转换为可复制文字的 PDF。

### 4. PPTX 解析内容很少

如果幻灯片主要是图片、截图或复杂图表，python-pptx 只能提取文本框里的文字。可以先把关键信息放进文本框，或后续加入 OCR。

### 5. 生成速度很慢

本地大模型速度取决于电脑性能和模型大小。可以尝试：

- 换用更小模型
- 调小“每个分块最大字符数”
- 上传更短的课件

### 6. 文件过大

当前 MVP 默认限制 80 MB。可以拆分课件后分别生成复习材料。

## 数据保存位置

- 历史记录数据库：`data/study_history.db`
- 手动导出的 Markdown：`generated_exports/`

## 后续可扩展方向

- 增加 OCR，支持扫描版 PDF 和图片型 PPT
- 增加章节级导航和来源跳转
- 增加题目数量、题型和难度设置
- 增加多模型对比
- 增加应用图标、自动更新和安装包签名
