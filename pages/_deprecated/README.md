# 过时文件（_deprecated）

**目录**：旧 Streamlit 页面（中文化版本）

**废弃原因**：Phase 26 已将项目从 Streamlit 迁移到 FastAPI + Jinja2 + HTMX（2026-08-31），新入口为 `cd web && python -m uvicorn app:app --port 8530`，旧 Streamlit 页面不再使用。

**文件**：
- `00 首页.py`
- `01 内容工坊.py`
- `02 内容诊断.py`
- `03 内容预测.py`
- `04 历史洞察.py`
- `05 真实结果回流.py`

**创建时间**：2026-08-28 ~ 2026-08-31（Phase 26 期间 Windows 本地修改）

**未 commit 过**：git history 中无任何 commit 包含这些文件，归档时直接从 `pages/` 移入本目录。

**处置**：保留作为历史参考，不删除。如需清理可整体删除本目录。