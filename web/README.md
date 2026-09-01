# MCD AI 内容平台 · Web 骨架（v2 · FastAPI + Jinja2 + HTMX）

> 状态：**首页 + 全局框架完成**，01-05 占位。  
> 旧版 Streamlit 代码保留在父目录 `C:\ideon\mcd-ai-content-platform\`，独立可跑。

## 启动

```bash
cd C:\ideon\mcd-ai-content-platform\web
pip install -r requirements.txt
uvicorn app:app --reload --port 8530
```

浏览器打开 <http://localhost:8530/>

健康检查：<http://localhost:8530/health>

## 目录结构

```
web/
├── app.py                    FastAPI 入口（路由 + 模板上下文）
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html             全局骨架（侧栏 + 顶栏 + footer）
│   ├── home.html             首页正文
│   └── pages/
│       ├── 01_内容工坊.html  占位（建设中）
│       ├── 02_文案诊断.html
│       ├── 03_批量评估.html
│       ├── 04_历史洞察.html
│       └── 05_真实结果回流.html
└── static/
    └── css/
        └── style.css         从 v2.html 抽出的 CSS（严格保持视觉）
```

## 视觉来源

CSS 来自 `C:\Users\a952462\OneDrive - ATOS\桌面\mcd_ai_content_platform_ui_v2.html`，
原样抽取，**没有改动任何配色 / 圆角 / 阴影 / 间距**。

## 关键技术决策

1. **不用 React / Vue / 任何前端构建工具链**——Jinja2 模板 + HTMX 局部刷新。
2. **侧栏高亮在后端控制**——`active_id` 由路由注入，避免客户端 JS。
3. **CSS 与 HTML 分离**——`static/css/style.css` 单文件，方便后续主题切换。
4. **响应式断点保留**——1100px / 760px 两档，参考 v2 原稿。
5. **顶部 topbar 的 `top-actions` 区保留为空**——未来 portal 部署时由 portal 统一管。

## 把 Streamlit 函数搬过来时改哪些地方

| Streamlit | FastAPI + Jinja2 等价做法 |
|---|---|
| `st.set_page_config(layout="wide")` | base.html 已 `width: calc(100% - 228px)` 等同 |
| `st.markdown("<h1>...</h1>", unsafe_allow_html=True)` | 直接在模板里写 `<h1>` |
| `st.metric(label, value, delta)` | 手写 `<div class="metric">`（见 home.html 4 个 metric 块） |
| `st.dataframe(df)` | `df.to_html(classes='data-table', border=0, index=False)` |
| `st.file_uploader("csv", type="csv")` | `<form enctype="multipart/form-data"><input type="file">` + `hx-post` |
| `st.selectbox("xxx", options)` | `<select name="x">{% for o in options %}<option>{{o}}</option>{% endfor %}</select>` |
| `st.button("生成", on_click=fn)` | `<button hx-post="/api/xxx" hx-target="#result">` |
| `st.spinner("...")` | `hx-indicator` + CSS spinner |
| `st.progress(0.5)` | HTMX `hx-trigger="every 500ms"` 轮询 `/api/progress` |
| `st.tabs([...])` | URL hash 路由 or 纯客户端 + HTMX 懒加载 |
| `st.session_state` | cookie / URL param / Redis（按场景选） |
| `@st.cache_data(ttl=60)` | `@functools.lru_cache(maxsize=128)` 或自建 TTL 装饰器 |
| `inject_base_css()` | 已经在 base.html 头部 `link style.css`，无需手动注入 |

## HTMX 用法示例（01 内容工坊已写在注释里）

```html
<!-- 模板里的按钮 -->
<button hx-post="/api/01/generate"
        hx-target="#candidates"
        hx-include="[name='task_json']"
        hx-swap="innerHTML">
  生成 3 条候选
</button>
<div id="candidates">点击后这里会被替换</div>
```

```python
# app.py 里的对应路由
@app.post("/api/01/generate", response_class=HTMLResponse)
async def api_01_generate(request: Request):
    form = await request.form()
    # 调 services/generation_service.generate_candidates(...)
    return HTMLResponse("<div class='candidate-card'>...</div>")
```

## 跟父目录 Streamlit 项目的关系

| 路径 | 状态 | 备注 |
|---|---|---|
| `../pages/0X_*.py` | 保留 | Streamlit 版本仍在跑（端口 8510 / 8520） |
| `../ui/styles.py` | 保留 | 仅 Streamlit 引用 |
| `../services/` | **直接复用** | 业务逻辑（CTR 预测、规则、文案分析）原样 import |
| `../repositories/` | **直接复用** | SQLite / DB 访问 |
| `../adapters/` | **直接复用** | 旧项目适配器 |
| `../core/` | **直接复用** | schemas / LLM gateway |

**新项目调旧项目的纯函数零成本**——只需要改 UI 渲染层。

## 下一步

- [ ] 把 01 内容工坊从 Streamlit 迁过来（878 行，最复杂，验证整体可行性）
- [ ] 把 02-05 依次迁移
- [ ] 把 `services/`、`adapters/` 接到 FastAPI 路由
- [ ] 部署到内网（参考 `C:\ideon\IDeon-项目全流程-Handoff.md` 的 nginx + systemd 配置）