# mcd-ai-content-platform — 教训（避坑全集）

> **何时读我**：写代码踩了坑 / 准备做新模块前，按关键词搜这里。
> 索引在 `Handoff.md` §6（"教训"段）+ 本文件目录。

---

## 目录（按 Phase 倒序）

- [`@lru_cache` + 测试 monkey-patch 陷阱](#lru_cache--测试-monkey-patch-陷阱)（2026-08-26 · Phase 6 P3）
- [手写 yaml 解析器 vs PyYAML](#手写-yaml-解析器-vs-pyyaml)（2026-08-26 · Phase 6 P3）
- [决策文档驱动开发](#决策文档驱动开发)（2026-08-26 · Phase 6 P1）
- [Streamlit widget 灰态实战](#streamlit-widget-灰态实战)（2026-08-26 · Phase 6 P1）
- [dataclass 字段顺序铁律](#dataclass-字段顺序铁律)（2026-08-26 · Phase 6 P1）
- [CTR 学习 ≠ 复杂模型 · 务实主义](#ctr-学习--复杂模型--务实主义)（2026-08-26 · §5.5 衍生教训）
- [Candidate.title 允许为空](#candidatetitle-允许为空)（2026-08-24 实战）
- [Python 字符串嵌套双引号](#python-字符串嵌套双引号)（2026-08-24 实战）
- [st.Page("app.py") 自引用递归](#stpageapppy-自引用递归)（2026-08-24 实战）
- [github 推送](#github-推送)
- [PowerShell 编码](#powershell-编码)
- [verify.py 用例数从 82 → 152](#verifypy-用例数从-82--152)（2026-08-24 实战）
- [极简 yaml 解析行内注释陷阱](#极简-yaml-解析行内注释陷阱)（2026-08-26 实战）
- [GitHub secret scanning 阻断 push](#github-secret-scanning-阻断-push)（2026-08-26 实战）
- [verify.py CSV bytes literal 限制](#verifypy-csv-bytes-literal-限制)（2026-08-26 实战）
- [CTR Adapter _demo_pred bl=None 兜底](#ctr-adapter-_demo_pred-blnone-兜底)（2026-08-26 实战）
- [Candidate.id=A/B/C 校验](#candidateidabc-校验)（2026-08-26 实战）
- [diagnose_problems 参数陷阱](#diagnose_problems-参数陷阱)（2026-08-24 实战）
- [analyzer.py → text_analyzer.py 脱 Streamlit](#analyzerpy--text_analyzerpy-脱-streamlit)（2026-08-24 实战）
- [setup_and_run.bat 双标签](#setup_and_runbat-双标签)（2026-08-24 实战）
- [OneDrive + git](#onedrive--git)
- [bat 文件 LF vs CRLF 换行符](#bat-文件-lf-vs-crlf-换行符)（2026-08-24 实战第 6 次闪退）
- [`setup_and_run.bat` 闪退 5 次迭代](#setup_and_runbat-闪退-5-次迭代)（2026-08-24 实战）

---

## 7. 教训（避坑）## 7. 教训（避坑）

### `setup_and_run.bat` 闪退 5 次迭代（2026-08-24 实战）

**最终方案 v5**：跳过 venv，用系统 Python（依赖已装好），`python -m streamlit run app.py`。

**失败历史**：
1. **v1 chcp 65001 闪退**：Win11 cmd 子系统切换 UTF-8 在某些环境崩
2. **v2 netstat -ano 找不到**：Win11 默认禁用 netstat
3. **v3 `call venv\Scripts\activate.bat` 损坏**：venv 损坏导致 cmd 把 activate.bat 内容当命令执行（`'form' / 'use' / 'ho' 不是内部命令`）
4. **v4 GBK 编码问题**：脚本含中文，cmd 用 GBK 解码乱码
5. **v5 跳过 venv**：系统 Python 已有依赖，直接 `python -m streamlit run`

**铁律**：bat 文件**只用 ASCII**（含 `setlocal enabledelayedexpansion` 支持 `!VAR!`）；每个 `exit /b` 前 `pause`；最后成功也 `pause`；不依赖 `where` / `netstat`，用 PowerShell 替代。

### bat 文件 LF vs CRLF 换行符（2026-08-24 实战第 6 次闪退）

**症状**：v5 bat 跑起来报 `'form' / 'dexpansion' / 'Platform' / 'k' 不是内部或外部命令`，cmd 把整段当一行命令执行。

**真因**：bat 文件用 LF（`\n`）换行，cmd **严格要求 CRLF**（`\r\n`）。Write 工具默认 UTF-8 LF，commit 时 git 还提醒 `LF will be replaced by CRLF`——但当时没人注意到这个 warning 已经把文件存成了 LF。

**检测**：`grep -c $'\r' setup_and_run.bat` ≥ 1 才是 CRLF，= 0 是 LF-only 闪退风险。

**修复**（一次性 Python 脚本）：
```python
p = 'setup_and_run.bat'
content = open(p, 'rb').read()
fixed = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
open(p, 'wb').write(fixed)
```

**铁律**：所有 Windows bat 必须 **CRLF**；新建 bat 后立刻 `grep -c $'\r' 文件.bat` 验证 ≥ 1，否则必闪退。

### OneDrive + git
`C:\ideon` 不是 OneDrive 同步目录，git 正常。搬 OneDrive 后按 memory `feedback-onedrive-git` 恢复。

### setup_and_run.bat 双标签（2026-08-24 实战）
`start "" explorer.exe "http://..."` + `streamlit --server.headless=false` → 各开一个浏览器 tab。
正确做法：删 explorer 行，让 Streamlit 自己用 webbrowser 模块开浏览器（headless=false 默认行为）。

### analyzer.py → text_analyzer.py 脱 Streamlit（2026-08-24 实战）
- `@st.cache_data` 全替 `@functools.lru_cache(maxsize=N)`，注意 frozenset 不能放 lru_cache（需 tuple 装返回）+ 字典读 file 时路径要 fallback（参数注入）
- `dict_counts()` 旧实现读 `st.session_state` 返回实时 staging 数。脱 Streamlit 后改成 `dict_counts(staging_dict=None, staging_ban=None)`，UI 层从 `st.session_state.get(...)` 取出传入——保持语义不变、不丢功能
- `frozenset` 替 `set`：放进 pandas `apply(axis=1)` 的 Series 时，**frozenset 比 set 安全**（避免 set 在 dataframe 操作中被冻结抛 Unhashable）

### diagnose_problems 参数陷阱（2026-08-24 实战）
`diagnose_score(...)` 返回 `{"diag": local_diagnose_dict, ...}`。调用 `diagnose_problems(title, body, diag)` 时 `diag` 必须是 **local_diagnose dict**（含 `len_title` / `len_body` / `emoji_count` / `hit_words` / `miss_top`），不是 score 顶层 dict。
- 正确写法：`diagnose_problems(t, b, score_result["diag"])`
- 错误写法：`diagnose_problems(t, b, score_result)` → `KeyError: 'len_title'`

### Candidate.id=A/B/C 校验（2026-08-26 实战）
`Candidate.__post_init__` 强制 id ∈ {"A","B","C"}（PRD §9.2 输出 schema）。所以 `predict_one` 之类的入口 B 不能走 Candidate 包装，必须直接构造 row dict 调 `adapter.predict_batch`：
- 错：`Candidate(id="X", strategy="diagnose", ...)` → `ValueError`
- 对：`adapter.predict_batch([{"channel":..., "title":..., "body":..., ...}])`

### CTR Adapter _demo_pred bl=None 兜底（2026-08-26 实战）
原 `_demo_pred` 第 184 行直接 `bl*100:.2f`，但 `baseline_lookup` 找不到维度组合时 `_safe_ctr("未知")` 返回 None，`None*100` 抛 TypeError。
- 入口 B 触发率 100%（无历史数据时必然 bl=None）
- 修复：bl=None 时显示"无基准"；pred_ctr 兜底 0.02

### verify.py CSV bytes literal 限制（2026-08-26 实战）
Python `b"..."` 字面量只能含 ASCII。中文字符串测试数据要 `.encode("utf-8")`：
- 错：`b"title,body,channel\n标题,内容,APP Push\n"` → `SyntaxError`
- 对：`"title,body,channel\n标题,内容,APP Push\n".encode("utf-8")`

### GitHub secret scanning 阻断 push（2026-08-26 实战）
`tools/push_via_api.py` 硬编码 GitHub PAT 触发了 GitHub 的 secret scanning 规则 → push 被 `remote rejected`。
- **症状**：`error: failed to push some refs ... (push declined due to repository rule violations)` + `path: tools/push_via_api.py:17` 提示"remove secret from commit(s)"
- **修复**：token 改成从环境变量 `GITHUB_TOKEN` / `GH_TOKEN` 读，或 `--token` CLI 参数；amend commit 覆盖后 force-with-lease 推上去
- **铁律**：任何工具脚本里**不要硬编码 token / API key / 私有证书**——既不安全也会被 GitHub 阻断 push

### 极简 yaml 解析行内注释陷阱（2026-08-26 实战）
`ui/llm_status._read_yaml` 第一版只 `partition(":")` + `strip`，没处理**行内 # 注释**。当 yaml 写 `provider: ""  # 例: "openai"` 时，注释文字被当成 value，结果 `is_configured()` 误判 True。
- **症状**：默认全空状态 is_configured() 返回 True，missing_fields() 返回空
- **修复**：value 端要先 `split("#", 1)[0]` 砍注释，再 strip + 去引号
- **铁律**：手写 yaml 解析必须处理 4 类边界——整行 `#` 注释 / 行内 `#` 注释 / 引号包裹 / 空字符串

### verify.py 用例数从 82 → 152（2026-08-24 实战）
Phase 2 新增 11 个测试函数（§13-23，共 70 用例）。跑测试要 `PYTHONIOENCODING=utf-8`，否则 `_check()` 的 emoji 中文会撞 GBK codec（不是 bug，但中断 print 流导致用例数不准）。

### PowerShell 编码
Windows 上 WriteAllText+UTF8Encoding($false)。Claude Code Write 工具默认 UTF-8 无 BOM，OK。

### github 推送
直连 `github.com`，gh-proxy.com 反代已 403。本地分叉用 `--force-with-lease`。

### st.Page("app.py") 自引用递归（2026-08-24 实战）
`app.py` 用 `st.navigation([st.Page("app.py", ...), ...])` + `pg.run()` → `RecursionError: maximum recursion depth exceeded`。Streamlit 把 app.py 自己也当页面执行，每次 exec 都会再调 pg.run() → 无限递归。

**修法**：app.py 只保留入口配置（`set_page_config` + `inject_base_css`），首页内容挪到 `pages/00_home.py`，用 `pages/` 自动发现（Streamlit 默认行为），**不要在 app.py 调 st.navigation / st.Page**。

### Python 字符串嵌套双引号（2026-08-24 实战）
LLM prompt 字符串里要嵌"引用"，**别直接 `"...\"X\"..."` 配 `\"` 转义**，Claude Code Write 工具容易错位导致 SyntaxError。

**修法**：用中文「」替代英文双引号——`"突出「专属」+「福利」命中企微 1v1 必带词"`。可读性更好且无转义负担。涉及：`services/generation_service.py:70` + `prompts/copy_rewrite.py:29/33`。

### Candidate.title 允许为空（2026-08-24 实战）
短信 / 企微 1v1 无独立标题，PRD §8.2 显式允许。`core/schemas.py:265` 校验必须放：`if not self.body.strip()`，**不要带 title 校验**。验证测试也要相应改成"title 空不抛错"。

### CTR 学习 ≠ 复杂模型 · 务实主义（2026-08-26 · §5.5 衍生教训）
第一直觉是"加神经网络预测 CTR"，但本场景 4 个硬约束直接排除：
- 输入特征是**结构化表格**（渠道/人群/阶段/场景 + 字数 + emoji + 命中词），不是文本/图像
- 样本量是**几千到几万**（麦当劳业务体量），不是亿级
- **可解释是刚需**——业务要能问"为什么这个 Plan CTR 高"，GBDT 给特征重要性，DNN 给一堆注意力
- LLM 在旁主攻**生成**，CTR 模型只替**预测**这一层，两个职责清

→ **L1 选 LightGBM/XGBoost 几乎无悬念**；L2 增量重训也走这套路。DeepFM/DIN/Transformer 全上都是过度设计。

**铁律**：加新模型前先问三句——(1) 这是结构化还是非结构化？(2) 样本量级够哪个量级？(3) 可解释是不是刚需？三句里如果有 2 句答"结构化/中样本/是"，**别上深度**。

### dataclass 字段顺序铁律（2026-08-26 实战 · Phase 6 P1）
Python dataclass 强约束：**所有带默认值的字段必须在所有无默认值的字段之后**。
Phase 6 P1 把 `product_benefit` 切灰态改成 `str = ""`，但忘了挪位置，结果 `raise TypeError: non-default argument 'audience' follows default argument 'product_benefit'`，整页报错回不去。
- **修法**：`TaskInput` 改为 `[audience/channel/stage/scene/tone (no-default) + expected_action/plan_type/coupon/planned_send_date/extra_requirements (有默认) + product_benefit/objective (灰态有默认)]`——所有灰态字段挪到末尾
- **副作用 1**：`from_form` 仍然按 dict 关键字传，**参数顺序不影响**（只影响位置传参）
- **副作用 2**：用 `try TaskInput.from_form(空 form) except ValueError` 校验必填——直接抛错就够，不必绕一圈
- **铁律**：改 dataclass 字段默认值前 (1) 看字段顺序、(2) 不要默认空串和 no-default 混、(3) 改完跑全套 verify.py 别靠肉眼

### Streamlit widget 灰态实战（2026-08-26 · Phase 6 P1）
决策文档说视觉："整体降透明度（如 opacity 0.5）+ 右上角小角标 + hover tooltip"——Streamlit 没暴露 widget 级 opacity 钩子。
**实用近似**：
1. `disabled=True`（Streamlit 自己会灰化控件，符合预期）
2. label 加「待开发·二期接入」（文字角标代替 CSS 角标）
3. `help="后续开放，敬请期待"`（自动 hover tooltip）

三层叠加视觉差异足够清晰。剩下 10% 视觉差用顶部 banner（`.advanced-notice`）+ 00_home 卡片分组补。
**铁律**：Streamlit 控件别追 100% CSS 还原；用 disabled / label / help / banner 四件套覆盖 > 90% 场景。

### 决策文档驱动开发（2026-08-26 · Phase 6 P1）
另一个 AI 提醒的 `Downloads\Demo范围决策与待确认_2026-08-26.md` 定义了"本轮只动 6 维度灰态 + 4 页面弱化 + CTR 反哺免责，不动后端反哺 / 不删任何页面 / 不接真实数据"。
**严格按文档边界执行**——本轮没碰 P3/P4/demo 回灌/pytest 候选（虽然看着诱人），等业务确认 7 项清单再说。
**启示**：用户或另一个 AI 留的"范围/边界/决策"文档 = 当前轮的 scope-control，**不要按"全局规划"自己加码**。
**铁律**：接活前先 grep `/c/Users/a952462/Downloads/` 找决策/范围/边界 md 文件；找到了就以它为准，无就走 PRD / Handoff 默认。

### `@lru_cache` + 测试 monkey-patch 陷阱（2026-08-26 · Phase 6 P3）
`_load_yaml()` 加 `@functools.lru_cache(maxsize=1)` 后，测试 `ls.CONFIG_PATH = type(...)(新路径)` 改路径但 cache 仍命中首次调用的旧路径内容。
- **症状**：3 个 `_check` 全 FAIL——"全填 is_configured() == True" / "全填 missing_fields() == []" / "部分空 missing_fields 2 字段"
- **修法**：测试在每次 monkey-patch `CONFIG_PATH` 后调 `ls._load_yaml.cache_clear()`（4 处），让下次读取走新路径
- **铁律**：测试里改任何被 `lru_cache` 捕获的依赖（路径 / env / module-level dict），改完必 `cache_clear()`——`@lru_cache` 是按参数 hash 的，**闭包内全局变量不在 hash key 里**

### 手写 yaml 解析器 vs PyYAML（2026-08-26 · Phase 6 P3）
`ui/llm_status.py` v1 用 30 行手写解析（4 类边界：整行注释 / 行内注释 / 引号包裹 / 空串）。Handoff §7 已录"行内 # 注释陷阱"教训——**那本身就是过度设计的代价**。
- **现状**：`services/rule_engine.py:54-56` 已用 `yaml.safe_load` 加载 `channel_rules.yaml` / `brand_rules.yaml`，PyYAML 在 `requirements.txt` 已是依赖
- **修法**：删 30 行手写解析，1 行 `yaml.safe_load` 替——4 类边界 PyYAML 自动处理，教训条目同时作废
- **铁律**：项目里已有 yaml 用法就别自己造轮子；新模块加载 yaml 前先 grep `yaml.safe_load` 是否有先例

---
