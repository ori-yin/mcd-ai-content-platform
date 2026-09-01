# mcd-ai-content-platform · 设计规范

> 目的：把首页 + 内容工坊里那一套"看着像个产品"的观感，抽象成可复用的设计语言，
> 让 02 文案诊断 / 03 批量预测 / 04 历史洞察 / 05 真实结果回流 / LLM 配置 modal 都跟它们对齐。
>
> **适用范围**：FastAPI + Jinja2 + HTMX 后的所有 5 页面 + 9 partial + 1 modal（`web/templates/`）
>
> **不适用范围**：旧 `pages/0X_*.py`（Streamlit，已 Phase 26 fallback，本规范不为它对齐）

---

## 0. 设计原则（4 条铁律 · 写任何页面之前先读）

| # | 原则 | 解释 |
|---|------|------|
| 1 | **复用优先** | 已有类名直接用，不新建 inline `style="..."` 顶替 |
| 2 | **中性留白** | 主色只有黑白黄绿，间距靠 `--radius` + `gap` 系列，不靠色块分隔 |
| 3 | **数字优先** | KPI / 表格 / 预测结果用大字号 + 单色，对比靠 `gap` 不靠 `border` |
| 4 | **无 emoji** | 图标一律 SVG（`/static/img/mcdonalds.svg` + inline 24×24 路径），状态用文字（✓ ! ✗） |

---

## 1. 设计 Token（CSS 变量 · `style.css:7-17`）

### 1.1 颜色（8 个）

```变量
:root {
  --bg:        #f6f7f8   /* 页面背景 */
  --panel:     #ffffff   /* 卡片 / 面板背景 */
  --line:      #e8eaed   /* 细分隔线 */
  --line-strong: #dde1e5 /* 表头 / 输入框边框 */
  --text:      #20242a   /* 正文 */
  --muted:     #737982   /* 次要文字（描述 / 标签） */
  --soft:      #f1f3f5   /* hover / 二级块底色 */
  --yellow:    #d9a72b   /* 主色（focus / 主按钮） */
  --green:     #43ad73   /* 成功状态点 / LLM 已连接 */
  --black:     #1d2228   /* 深色块（首页主 CTA） */
  --radius:    12px      /* 默认圆角 */
}
```

**派生色（写在 .css 不用变量，但锁死不要改）**：
- `warning-banner` 背景 `#fef7e8` + 边框 `#f0d68a` + 文字 `#7a5b0a`
- `success-banner` 背景 `#f0faf3` + 边框 `#b8e6c4` + 文字 `#1d6a3e`
- `code-wrap` 背景 `#f8f9fa`
- modal mask `rgba(29,34,40,.45)` + `backdrop-filter:blur(3px)`

### 1.2 字号（10 个梯度）

| 用途 | 字号 | 字重 | 行高 | 类 |
|---|---|---|---|---|
| 页面大标题 | 32px | 680 | — | `.page-title` |
| 卡片标题 | 18px | 650 | — | `.card-title` / `.section-heading` |
| 面板标题 | 17px | 650 | — | `.panel-heading` |
| modal 标题 | 16px | 680 | — | `.modal-title-text b` |
| 副标题 | 14px | 400 | — | `.subtitle` |
| nav 项 | 14.5px | 500 | — | `.nav-item` |
| 表单标签 | 12px | 600 | — | `.form-row label` / `.modal-card label>span` |
| 卡片描述 | 12.5px | 400 | 1.6 | `.card-desc` |
| 表格头 / 提示 | 12px | 600 | — | `.batch-table th` / `.warning-banner` |
| footnote | 11.5px | 400 | — | `.kpi-tile .sub` / `.metric-box .md` |

**字重档位**：400 / 500 / 600 / 650 / 680（**不用 700**，因为 680 配 700 的中文字看上去更齐）

### 1.3 间距

| 用途 | 间距 |
|---|---|
| `.main` 左右 padding | 40px |
| `.content` 底部 | 36px |
| `.card` padding | 30px |
| `.panel-card` padding | 默认 30px（视场景 14/20） |
| grid gap | 12px |
| form gap | 14px |
| subsection 间距 | 22px |
| 行内元素 gap | 8/10px |

### 1.4 圆角

| 场景 | 圆角 |
|---|---|
| 卡片 / 面板 / modal | `var(--radius)` = 12px |
| 输入框 / 按钮 / tab | 8px |
| chip / pill / 状态点 | 6px |
| 头像 / 圆形 icon | 50% |

---

## 2. 原子组件（13 个 · 单类即可用）

### 2.1 卡片壳

```html
<!-- 主页面用 -->
<section class="card hero">...</section>
<section class="card advanced-card">...</section>
<section class="card section-card">...</section>

<!-- 子页面用 -->
<section class="panel-card">...</section>
```

**区别**：`.card` 首页偏展示（hero / advanced / section），`.panel-card` 子页面偏业务（form + 表格容器）。

### 2.2 标题三层

```html
<!-- 整页大标题（topbar 唯一） -->
<div class="page-title">内容工坊</div>
<div class="subtitle">副标题（可空）</div>

<!-- 卡片 / section 标题 -->
<div class="card-title">关键决策</div>
<div class="section-heading">项目状态</div>

<!-- 面板 / 子模块 标题 -->
<div class="panel-heading">1 定义经营任务</div>
```

### 2.3 文字描述（两种）

```html
<!-- 卡片下描述（首页） -->
<div class="card-desc">一段话介绍</div>

<!-- 面板下描述（子页面） -->
<div class="card-desc">必填 3 项，其余默认「通用」</div>
```

> **注**：两个都叫 `card-desc` 是历史选择，新代码遵循即可（不另起名）。

### 2.4 提示横幅（3 类）

```html
<!-- 警告（黄） -->
<div class="warning-banner">缺 body 列，无法启动评估</div>

<!-- 成功（绿） -->
<div class="success-banner">已保存到 ~/.mcd-ai/llm_settings.yaml</div>

<!-- Demo 模式（灰） -->
<div class="advanced-notice">Demo 模式：批量 CTR 预测走本地 + 历史基准</div>
```

**用法规范**：banner 一定放在对应内容块**顶部**，不要放中间或底部。

### 2.5 空态

```html
<div class="empty-state">诊断后此处显示渠道预览和 CTR 参考。</div>
```

### 2.6 表单（统一）

```html
<form method="post" action="/..." class="form-grid">
  <div class="form-row">          <!-- 默认单列 -->
    <label>渠道</label>
    <select name="channel">...</select>
  </div>
  <div class="form-row form-row-wide">  <!-- 跨双列 -->
    <label>正文</label>
    <textarea>...</textarea>
  </div>
</form>
```

**规则**：所有 form 表单一律 `class="form-grid"` + `form-row`，不要写 inline `display:flex`。

### 2.7 按钮（3 档）

```html
<!-- 首页主 CTA（链接版，黑底白字 + hover →） -->
<a href="/studio" class="primary-btn">进入 内容工坊 <span>→</span></a>

<!-- 业务主按钮（按钮版，黑底白字 47px） -->
<button type="submit" class="btn btn-dark btn-submit">开始诊断</button>

<!-- modal 内按钮（黄底黑字，匹配 modal 视觉系统） -->
<button type="button" class="btn-primary">应用配置</button>

<!-- 次要按钮 -->
<button type="button" class="btn-secondary">测试连接</button>

<!-- 紧凑查询按钮（04 tab 内 36px） -->
<button type="submit" class="btn btn-dark btn-sm">查询</button>
```

**规则**（Phase 37 统一）：
- **业务流统一 `.btn-dark` 黑底白字**（首页 + 内容工坊 + 02/03/04/05 全部）
- modal 内部独立视觉系统，保留 `.btn-primary` 黄底黑字（配合 modal 黄色 focus / 标签前缀圆点）

### 2.8 KPI / 数据展示（3 类）

```html
<!-- 大 KPI（数字 + 标签 + 描述） -->
<div class="kpi-tile">
  <div class="label">预测 CTR</div>
  <div class="value">2.34%</div>
  <div class="sub">基准 1.85% · +0.49pp</div>
</div>

<!-- 一排 KPI（多用 metric-row） -->
<div class="metric-row">
  <div class="metric-box"><div class="ml">总记录数</div><div class="mv">1,234</div></div>
  <div class="metric-box"><div class="ml">渠道数</div><div class="mv">3</div></div>
</div>

<!-- 首页项目状态 -->
<div class="metric">
  <div class="metric-icon">✓</div>
  <div>
    <div class="metric-label">数据接入</div>
    <div class="metric-value">完成</div>
  </div>
</div>
```

### 2.9 表格（2 类）

```html
<!-- 大表格（带滚动条 + 表头边框） -->
<div class="batch-wrap">
  <table class="batch-table">
    <thead><tr><th>标题</th><th>渠道</th></tr></thead>
    <tbody><tr><td>...</td></tr></tbody>
  </table>
</div>

<!-- 小表格（首页关键决策 / 验证命令） -->
<table>
  <tr><td>项目位置</td><td>mcd-ai-content-platform</td></tr>
</table>
```

### 2.10 状态徽章 / 圆点

```html
<span class="dot"></span>   <!-- 7×7 圆点，颜色用 var(--green) -->
<span class="l1-pill">L1 实验预测 1.16%</span>   <!-- 02/01 右侧专用 -->
<span class="status"><span class="dot"></span>已连接</span>
```

### 2.11 Tabs（04 专属）

```html
<div class="ins-tabs">
  <a href="/insights?tab=rank" class="ins-tab active">高效 Plan 排行</a>
  <a href="/insights?tab=wf"   class="ins-tab">高低表现词</a>
</div>
```

### 2.12 子区块（面板内的子分组）

```html
<div class="subsection">
  <div class="subsection-label">渠道预览</div>
  <!-- 内容 -->
</div>
```

### 2.13 输入框修饰（modal 专用）

modal 里的 `<label>` 自动有 4px 黄色圆点前缀（`.modal-card label>span::before`），无需手动加。

---

## 3. 分子组件（6 个 · 跨页面复用）

### 3.1 候选卡（candidate-card）

**01 内容工坊 + 02 文案诊断（AI 改写）共用**。

```html
<div class="candidate-card selected">
  <div class="cand-row">
    <div class="cand-header"><b>A</b> · 利益前置</div>
    <div class="cand-title">标题文本</div>
    <button class="btn-select">选 A</button>
  </div>
  <div class="cand-body">正文文本</div>
</div>
```

**布局**：1 列 3 行竖排，每张卡内**横排**：header(120px) + title(1fr) + button(90px)。
**已实现**：01 全部 3 张卡 + 02 改写 2 张卡均走这套。

### 3.2 渠道预览（preview-card / wechat-bubble）

**01 中栏 + 02 中栏共用**，3 种渠道渲染：

| 渠道 | 容器 | 关键元素 |
|---|---|---|
| APP Push | `.preview-card` | `.pv-meta` / `.pv-title` / `.pv-body` |
| 企微 1v1 | `.wechat-bubble-wrap` + `.wc-avatar` + `.wechat-bubble` | `.wc-name` / `.wc-title` / `.wc-body` |
| 短信 | `.preview-card`（无 title） | `.pv-meta` + 段数计算（`(len+69)//70`） |

**未实现**：微信公众号 / 抖音 / 其他渠道 → `warning-banner` 占位。

### 3.3 LLM 配置 Pill（llm_pill.html）

**全站右上角**，所有页面共享。

```html
<button class="model-select" onclick="document.getElementById('settings-modal-slot').innerHTML=''; htmx.ajax('GET', '/api/settings/llm', '#settings-modal-slot')">
  <span class="status"><span class="dot"></span>已连接</span>
  <svg class="chev">...</svg>
</button>
```

**规则**：点击 → HTMX GET 把 modal partial 塞 `#settings-modal-slot`。

### 3.4 LLM 配置 Modal（settings_llm_modal.html）

**全站可触发**，HTMX 局部刷新。

```html
<div class="modal-mask">
  <div class="modal-card">
    <div class="modal-header">...</div>
    <div class="modal-body">...</div>
    <div class="modal-foot">...</div>   <!-- i 开头的说明块 -->
  </div>
</div>
```

**规则**：mask 点击自身关闭（`onclick="if(event.target===this)...innerHTML=''"`），表单按钮走 `hx-post` + `hx-include="#llm-form"` + `hx-target="#settings-modal-slot"` 局部刷新。

### 3.5 顶部设置条（settings-bar）

**01 内容工坊专属**：顶部算法模型选择条。

```html
<div class="settings-bar">
  <form method="post" action="/api/studio/ctr-mode" class="settings-form">
    <label class="settings-label">算法模型</label>
    <select name="ctr_mode" onchange="this.form.submit()">
      <option value="demo">演示规则</option>
      <option value="baseline_only">历史基准</option>
      <option value="l1_model">LightGBM</option>
    </select>
  </form>
</div>
```

### 3.6 L1 预测 Pill（l1-pill）

**01 右栏 + 02 CTR 卡** 专属展示 L1 实验预测。

```html
<div class="l1-pill">
  <span class="l1-label">L1 实验预测</span>
  <span class="l1-value">1.16%</span>
  <span class="l1-meta">LightGBM · logit 反变换</span>
</div>
```

3 态：`.l1-pill`（有值）/ `.l1-pill.muted`（模型暂不可用）/ `.l1-pill.muted`（渠道不在训练范围）。

---

## 4. 页面骨架（5 页 + 1 首页）

### 4.1 页面结构通式

```html
{% extends "base.html" %}
{% block title %}<页面名> · McD AI 内容平台{% endblock %}
{% block content %}

{# 顶部 banner（仅 demo 模式 / 上传成功后） #}
{% if not llm_configured %}<div class="advanced-notice">...</div>{% endif %}

{# 主内容面板（可多个）#}
<div class="panel-card">
  <div class="panel-heading">1 步骤名</div>
  <div class="card-desc">说明</div>
  {# 警告 / 成功 #}
  {# form / table / 内容 #}
</div>

{# 第二个面板 #}
<div class="panel-card" style="margin-top:14px">...</div>

{% endblock %}
```

### 4.2 各页面骨架差异

| 页面 | 顶部设置条 | 主布局 | 候选卡 | 渠道预览 | KPI / 表格 | L1 Pill |
|---|---|---|---|---|---|---|
| `00 home` | — | `.top-grid` 2 列 + `.bottom-grid` 2 列 | — | — | 4 metric | — |
| `01 studio` | `.settings-bar` | `.studio-grid` 3 列 | ✓（3 张） | ✓（中） | — | ✓（右） |
| `02 diagnosis` | — | `.diag-grid` 3 列 | ✓（2 张改写） | ✓（中） | 1 kpi-tile + 1 batch-table | ✓（中） |
| `03 batch` | — | 单列 + panel-card 串联 | — | — | 5 metric-box + 1 batch-table | — |
| `04 insights` | — | panel-card + `.ins-tabs` + `.ins-panel` | — | — | 4 metric-box + 多 batch-table | — |
| `05 feedback` | — | 4 panel-card 串联 | — | — | 4 metric-box + 2 batch-table | — |

### 4.3 网格列宽约定

| 网格 | 列宽 | 场景 |
|---|---|---|
| `.top-grid` | 42% / 58% | 首页 hero + 进阶能力 |
| `.bottom-grid` | 1fr / 1fr | 首页关键决策 + 验证命令 |
| `.advanced-grid` | repeat(4, 1fr) | 进阶能力 4 项 |
| `.status-grid` | repeat(4, 1fr) | 项目状态 4 metric |
| `.metric-row` | repeat(5, 1fr) | KPI 一排 5 |
| `.studio-grid` | 1fr / 1.6fr / 1.3fr | 内容工坊 3 列 |
| `.diag-grid` | 1fr / 1.05fr / 1.1fr | 文案诊断 3 列 |

---

## 5. 当前不一致项（待 Phase 37 收敛）

> Phase 36 审计发现，下面 3 处仍有"贴板"问题，建议下次开会拍板后一次性收敛。

| # | 文件 | 问题 | 建议收敛 |
|---|---|---|---|
| 1 | `partials/02_similar_rewrites.html:60` | `.cand-body` 上 inline `style="margin-top:6px;font-size:12px;color:#888"` | 抽出 `.cand-meta` 类（或用 `.subsection-label`） |
| 2 | `partials/02_rule_panel.html:51, 52` | 行内 `<div style="font-size:12.5px;margin-bottom:4px;color:#3a4049">` | 抽出 `.stat-line` 类 |
| 3 | `partials/02_rule_panel.html:57` | 行内 `<div style="margin-top:10px">` | 改成 `.subsection` 类（已有 22px top margin） |

---

## 6. 复用指引（添加新页面 / 新模块时）

### 6.1 加一个 panel

```html
<section class="panel-card" style="margin-top:14px">   <!-- 默认 14px 间距 -->
  <div class="panel-heading">N 步骤名</div>
  <div class="card-desc">一段话说明</div>
  <!-- 内容 -->
</section>
```

### 6.2 加一个 KPI 一排

```html
<div class="metric-row" style="grid-template-columns:repeat(3,1fr)">  <!-- 改列数 -->
  <div class="metric-box">
    <div class="ml">标签</div>
    <div class="mv">数字</div>
    <div class="md">说明</div>
  </div>
</div>
```

### 6.3 加一个表单

```html
<form method="post" action="/..." class="form-grid">
  <div class="form-row">
    <label>字段名 *</label>
    <select name="x"><option>...</option></select>
  </div>
  <div class="form-row form-row-wide">
    <label>多行字段</label>
    <textarea>...</textarea>
  </div>
  <div class="form-row form-row-wide">
    <button type="submit" class="btn btn-primary" style="height:40px;width:200px;justify-content:center">
      提交 →
    </button>
  </div>
</form>
```

### 6.4 加一个表格

```html
<div class="batch-wrap">
  <table class="batch-table">
    <thead><tr><th>列1</th><th>列2</th></tr></thead>
    <tbody>{% for r in rows %}
      <tr><td>{{ r.c1 }}</td><td>{{ r.c2 }}</td></tr>
    {% endfor %}</tbody>
  </table>
</div>
```

### 6.5 加一个 banner

```html
{% if success_msg %}<div class="success-banner">{{ success_msg }}</div>{% endif %}
{% if error_msg %}<div class="warning-banner">{{ error_msg }}</div>{% endif %}
{% if info %}<div class="advanced-notice">{{ info }}</div>{% endif %}
```

### 6.6 加一个 modal（HTMX 局部刷新）

参照 `partials/settings_llm_modal.html`：`modal-mask > modal-card > modal-header / modal-body / modal-foot`。
**关键属性**：`hx-post` + `hx-include="#form-id"` + `hx-target="#slot-id"` + `hx-swap="innerHTML"`。

---

## 7. 演进路线（按返工风险梯队）

| 优先级 | 内容 | 触发条件 |
|---|---|---|
| P0 | **静态 lint**：扫 `templates/` 下所有 inline `style="..."`，3 条问题先收敛 | 改下一个新页面之前 |
| P1 | **新增 `.stat-line` / `.cand-meta` 类**：02 行内样式抽类 | P0 完成后批量改 |
| P2 | **modal 抽取为宏**：4 个 modal（LLM / 上传确认）共用 `{% include "partials/modal_frame.html" %}` | 第 3 个 modal 出现时 |
| P3 | **图标系统**：现有 SVG 都内联在 base.html nav，9+ 处 inline SVG 可抽 `{% include "partials/icon.html" name="..." %}` | UI 重设阶段 |
| P4 | **Dark mode**：基于 token 改 `--bg/--panel/--text` 三件套即可，组件层 0 改动 | 业务方拍板后 |

---

## 8. 反模式（不要做）

| ❌ 不要 | ✅ 应该 |
|---|---|
| `<div style="font-size:12px;color:#888">` | 用 `.subsection-label` / `.card-desc` |
| `<div style="display:flex;gap:10px">` | 用 `.form-row` / `.metric-row` / `.advanced-grid` |
| `<span style="font-weight:bold">**加粗**</span>` | `<b>...</b>` 或类名自带 650 |
| 表格写 `<table style="border-collapse:collapse">` | 用 `.batch-table` / `.batch-wrap` |
| 主按钮写 `<button style="background:#000;color:#fff">` | 用 `.btn-primary` / `.primary-btn` |
| inline SVG 24×24 不带 class | 加 `class="ico"` 自动 `width:18px; height:18px` |
| 自己造一套 banner / KPI 样式 | 走 §2.4 / §2.8 三类现成的 |
| 给同一概念造新类名（如 `.warn-box` / `.tip-card`） | 用 `.warning-banner` / `.kpi-tile` |

---

## 9. 验证（CI 防退化）

加一个轻量 lint 到 `tests/verify.py §62`：

```python
def test_design_md_no_inline_style():
    """禁止 templates/ 下出现 inline style（除 dynamic 表达式）"""
    import re, pathlib
    pat = re.compile(r'style="[^"]*(?:font-size|background|color|display|gap|padding):')
    offenders = []
    for p in pathlib.Path('web/templates').rglob('*.html'):
        for i, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            if pat.search(line):
                offenders.append(f'{p}:{i}: {line.strip()[:80]}')
    assert not offenders, f'inline style 违规 {len(offenders)} 处：\n' + '\n'.join(offenders[:5])
```

> 这一条要配合 §5 列出的 3 个不一致项收敛一起上，否则先 lint 会全红。

---

## 附录 A：类名速查（48 个）

```
骨架    .app .main .topbar .content .footer .sidebar .brand
导航    .nav .nav-item .nav-ico .ico
通用    .card .panel-card .card-title .card-desc .panel-heading .section-heading .subtitle .page-title
文字    .subsection .subsection-label .empty-state
布局    .grid .top-grid .bottom-grid .studio-grid .diag-grid .advanced-grid .status-grid .metric-row .ins-tabs
交互    .primary-btn .btn-primary .btn-secondary .btn-select
表单    .form-grid .form-row .form-row-wide .form-row label
提示    .warning-banner .success-banner .advanced-notice
展示    .kpi-tile .metric .metric-box .metric-icon .metric-label .metric-value .metric-detail
       .advanced-card .advanced-item .advanced-icon .advanced-name .advanced-desc .advanced-arrow
       .preview-card .pv-meta .pv-title .pv-body
       .wechat-bubble-wrap .wechat-bubble .wc-avatar .wc-name .wc-title .wc-body .wc-meta
       .candidate-card .candidate-grid .cand-row .cand-header .cand-title .cand-body
       .l1-pill .l1-label .l1-value .l1-meta
       .model-select .dot .chev .avatar .settings-bar .settings-form .settings-label
       .info-card .code-wrap .code .line-no
表格    .batch-wrap .batch-table
Tabs    .ins-tab .ins-panel
状态    .status
Modal   .modal-mask .modal-card .modal-header .modal-title-text .modal-close .modal-body .modal-foot .modal-actions
```

---

## 附录 B：变更日志

| Phase | 日期 | 内容 |
|---|---|---|
| Phase 26 | 2026-08-31 | 从 v2.html 抽出第一版 CSS 落地 `static/css/style.css`，5 页面迁移到 FastAPI |
| Phase 27 | 2026-09-01 | LLM modal 完整化 + URL 语义化 + 删除冗余（L1 hint / 副标题） |
| Phase 36 | 2026-09-01 | 滚动恢复强化 + URL `/04` 收尾 |
| **本文件** | 2026-09-01 | **首次写 design.md，沉淀 §1-§9 规范 + §5 不一致清单** |