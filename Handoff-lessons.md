# mcd-ai-content-platform — 教训（避坑全集）

> **何时读我**：写代码踩了坑 / 准备做新模块前，按关键词搜这里。
> **本文件已压缩**（2026-08-31）：从 18 条精简到 8 条核心教训；删阶段性 bug + git log 已有的细节。

---

## 8 条核心教训

### 1. dataclass 字段顺序铁律（Phase 6 P1）

Python dataclass：**所有带默认值的字段必须在所有无默认值的字段之后**。
- 坑：`product_benefit` 改 `str = ""` 但忘了挪位置 → `TypeError: non-default argument 'audience' follows default argument 'product_benefit'`
- 铁律：改默认值前 (1) 看字段顺序、(2) 不要默认空串和 no-default 混、(3) 跑全套 verify.py 别靠肉眼

### 2. Streamlit widget 灰态 4 件套（Phase 6 P1）

决策要求"整体降透明度 + 右上角小角标 + hover tooltip"，Streamlit 没暴露 widget 级 opacity 钩子。**实用近似**：
1. `disabled=True`（控件灰化）
2. label 加「待开发·二期接入」（文字角标）
3. `help="后续开放..."`（hover tooltip）
4. 顶部 banner（`.advanced-notice`）+ 00_home 卡片分组

覆盖 > 90% 场景，剩下 10% 视觉差没必要追 100% CSS 还原。

### 3. `@lru_cache` + 测试 monkey-patch 陷阱（Phase 6 P3）

`_load_yaml()` 加 `@lru_cache(maxsize=1)` 后，测试改路径但 cache 仍命中旧路径 → 3 个 `_check` 全 FAIL。
- 修：测试 monkey-patch `CONFIG_PATH` 后必调 `ls._load_yaml.cache_clear()`
- 铁律：`lru_cache` 按参数 hash，**闭包内全局变量不在 hash key 里**

### 4. 手写 yaml 解析器 vs PyYAML（Phase 6 P3）

`ui/llm_status.py` v1 用 30 行手写解析（整行注释/行内注释/引号/空串 4 类边界）→ `yaml.safe_load` 1 行替（PyYAML 已在 requirements.txt）。
- 铁律：项目里已有 yaml 用法就别造轮子；新模块加载 yaml 前先 grep `yaml.safe_load` 是否有先例

### 5. GitHub secret scanning 阻断 push（Phase 5）

`tools/push_via_api.py` 硬编码 GitHub PAT 触发 secret scanning → push 被 `remote rejected`。
- 修：token 读环境变量 `GITHUB_TOKEN`/`GH_TOKEN` 或 `--token` CLI；amend commit + force-with-lease
- 铁律：工具脚本里**不要硬编码 token / API key / 私有证书**

### 6. CTR 学习 ≠ 复杂模型 · 务实主义（§5.5 衍生）

场景硬约束：结构化表格 + 中样本 + 可解释是刚需 → **LightGBM/XGBoost 几乎无悬念**；DeepFM/DIN/Transformer 全是过度设计。
- 铁律：加新模型前问三句——(1) 这是结构化还是非结构化？(2) 样本量级够哪个量级？(3) 可解释是不是刚需？三句里 2 句答"结构化/中样本/是"，**别上深度**

### 7. st.Page("app.py") 自引用递归（Phase 3.2）

`app.py` 用 `st.navigation([st.Page("app.py")])` + `pg.run()` → `RecursionError: maximum recursion depth exceeded`。
- 修：app.py 只保留入口配置（`set_page_config` + `inject_base_css`），首页挪 `pages/00_home.py`，用 `pages/` 自动发现（Streamlit 默认行为）

### 8. bat 文件必须 CRLF（Phase 3.2 第 6 次闪退）

cmd 严格要 CRLF；Write 工具默认 LF。
- 检测：`grep -c $'\r' 文件.bat` ≥ 1 才是 CRLF，= 0 是 LF-only 闪退风险
- 修：一次性 Python 脚本 `b'\n' → b'\r\n'`
- 铁律：所有 Windows bat 必须 CRLF；新建 bat 后立刻验证

### 9. 会话间记忆丢失：跑分析不写 Handoff = 等于没跑（2026-08-31）

**防**：
- 每次跑完 EDA / SHAP / 维度统计 / 业务指标分析 → 强制落档 `data/findings/<topic>_<date>.json + .md`
- Handoff.md §6.5 维护一个**历史发现索引**（path + 一句话结论）
- 每次开新 session 第一步：grep §6.5 看有没有遗漏
- 工具脚本必须复用现有解析，不重新实现

**铁律**：跑完不写 Handoff = 没跑。落档路径必须有规律（`data/findings/` 不是 `tmp/`）。

### 10. UI 标签 vs selectbox value 分离（2026-09-01 · Phase 27 漏改）

**坑**：Phase 27 把 CTR 模式 UI 标签改成产品话术（`演示规则/渠道基线/XGBoost`）时，**selectbox 的 `value` 也跟着写成 `xgboost`**，但 `CTRPredictionAdapter.VALID_MODES = ('existing_predictor', 'baseline_only', 'demo', 'l1_model', 'unavailable')` 只认 `l1_model`。前端能选、后端拒收、用户看 500 Internal Server Error。

**表现**：`POST /api/studio/generate` 走 `api_01_generate` → `predict_for_candidates(..., mode=ctr_mode)` → `CTRPredictionAdapter(mode=ctr_mode)` 抛 `ValueError: mode must be one of ...`，冒到 FastAPI 默认 handler 返回 500。

**铁律**：
- UI 改标签（display text）时，**selectbox 的 `value=` 必须保持后端能识别的常量**（display 和 value 解耦）
- 改 UI 文案前后，**grep VALID_MODES / VALID_* 等后端枚举常量**，确认 selectbox value 没漏
- 涉及 `CTRPredictionAdapter` / `LLM_PROVIDERS` / `CHANNELS` / `PLAN_TYPES` 等枚举常量的 UI 修改，**改完必须 curl 跑一遍主路径**（不能只肉眼看 UI 标签对不对）

**副坑**：uvicorn `--reload` 在 Windows 上常失效，**改完代码必须手动重启 server** 才生效（setup_and_run.bat 默认不带 `--reload`，所以双击 bat 是最稳的方式）。

### 11. Handoff 数字漂移 =「schema 改 → verify.py 同步改」铁律失效（2026-09-01 · Phase 38 A1-mid 复盘）

**坑**：Handoff §6.0 写 `847 PASS / 0 FAIL`，实际跑是 `842 PASS / 5 FAIL`。Phase 28 / Phase 30 改 schema 时 verify.py 没同步 5 处断言（必填 4→3 / PLAN_TYPES 3→4 / options_with_custom +1→+2 / llm_status 默认测试用真实 yaml / sweep stage 必填 → 选填）。

**铁律**：
- **schema / enum / 必填字段改动 → verify.py 同步改是「改文件清单」的硬约束**，不是「下次再说」
- 改 `ui/llm_status.py` / `core/product_benefit.py` 等带 lru_cache 的模块 → 测试必须 monkey-patch + cache_clear，**闭包变量不入 hash key**
- Handoff §6.0 数字每次写必现场跑一次（**不引用旧数字**）

**避坑指引**：
- 改 `core/schemas.py` 任何字段、enum、默认值 → 必跑 `python tests/verify.py`，有 FAIL 就修
- design.md §12.1 写明此坑；新 session 第一步 grep Handoff §6.0 数字 + 现场跑 verify，数字对不上就查 lessons

### 12. 跨文件改动必须「改一个测试一个」（2026-09-01 · Phase 38 A1-mid 流程教训）

**坑**：本次 A1-mid 一开始想「先改 CSS 全部 → 一次性 verify」，结果中间出了 1 处遗漏 inline（03 line 41）。如果**改完一类就 grep lint + verify**，能立刻发现。

**铁律**：**每次 Edit 完一个文件 → 立刻跑针对该文件的小验证**（grep inline style / py_compile / verify §对应段），不要攒一批改完再测。

**避坑指引**：
- 改 HTML → grep `style="..."` 残留
- 改 Python → `python -m py_compile`
- 改 schema / enum / 必填 → 立刻跑 `python tests/verify.py`
- 全部改完 → 最后跑一次完整 verify.py + curl 6 路由

### 13. archive 嵌套的脚本 ROOT 路径需 `.parent.parent.parent`（2026-09-01 · Phase 38 A1-mid 顺手修）

**坑**：push_via_api.py 脚本从 `tools/_archive/` 跑时，`Path(__file__).resolve().parent.parent` 只到 `tools/`（不是 repo root），导致 `local.exists()` 检查错误，把"添加文件"分支走成"删除文件"分支，422 BadObjectState。

**铁律**：archive 里的脚本 `ROOT` 计算 = `.parent.parent.parent`（多一层）适配 archive 嵌套。

**避坑指引**：
- 新写 `_archive/` 下的工具脚本：直接用 `.parent.parent.parent`，不要 `.parent.parent`
- 跑 push 脚本前先 Read ROOT 计算那行，确认从 archive 跑不会走"删除"分支

### 14. Cookie `path` 严格匹配陷阱（2026-09-02 · Phase 40）

**坑**：cookie `path=/settings` → 浏览器只在 `/settings` 精确路径下发送 cookie → `/api/settings/save/*` / `/api/settings/download/*` 不发送 → 全 401。**修**：改 `path=/`（覆盖整站）。

**铁律**：cookie `path` 设 `/`，除非有明确子域隔离需求。

**避坑指引**：
- 鉴权 cookie 一律 `path=/`，不要按"敏感路径"细分
- `/api/*` 跟 `/foo` 是兄弟路径，不存在父子包含关系
- 调试 cookie 鉴权：先 `chrome://settings/cookies` 看 cookie scope + 再看 Network request cookie header

### 15. HTML attribute 遇 `\n` 截断（2026-09-02 · Phase 42）

**坑**：HTML5 spec 规定 attribute value 遇 LF (`\n`) 截断。`{{ d.content | tojson }}` 输出 `"word1\nword2"`，HTML parser 在第一个 `\n` 处截断 attribute → 后面的内容丢失。**症状**：textarea 显示不全。

**铁律**：textarea / pre / script 等需要保留 `\n` 的内容，绝不放 HTML attribute，必须放 tag 内容（`<script type="application/json">` / `<pre>` / `<textarea>` 本身）。

**避坑指引**：
- 多行文本 → 用 `<script type="application/json">` tag + JS `JSON.parse(tag.textContent)`
- 不用 `<input value="...">` / `<div data-x="...">` 装多行
- 不用 `<textarea>` 的 `value` attribute（textarea 没有 value 属性，只能写文本节点）

### 16. textarea 不解析 HTML entity（2026-09-02 · Phase 41）

**坑**：Jinja autoescape + `| e` 双重 escape → `&#34;` / `&amp;` 等 entity 字符串写进 textarea → **浏览器 textarea 不解析 HTML entity**（与 `<input value="...">` 不同） → 显示成 `&#34;` 字面量。**症状**：textarea 显示 `&quot;` 而不是 `"`。

**铁律**：textarea 内容只能用纯文本，不能用 HTML escape。必须 JSON 序列化。

**避坑指引**：
- 不要在 textarea 标签内 / attribute 上用 `| e` / `| escape`
- 用 `{{ content | tojson }}` 输出到 `<script>` tag，JS 读后 `ta.value = JSON.parse(...)`
- 同样适用于 `<pre>` / `<code>` 内容

### 17. git autocrlf 叠加双 CR 坑（2026-09-02 · Phase 43）

**坑**：浏览器 textarea 写 LF + Windows git autocrlf=true 把 LF 转 CRLF + 文件已含历史 CRLF 残留 → commit 时叠加变成 `\r\r\n`（双 CR）。**症状**：git diff 显示 `^M^M` 但 UTF-8 不报错。

**铁律**：
1. 跨平台协作的文件，仓库里加 `.gitattributes` 强制 line ending（`*.txt text eol=crlf` / `*.py text eol=lf`）
2. 服务端写文件前必须 normalize（`replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")`）
3. 用 bytes 操作，不用 str `.replace()`（后者只匹配单字符）

**避坑指引**：
- 任何写文本文件的服务端函数：bytes level CRLF 统一
- 看 GitHub diff 出现 `^M`：`git show HEAD:path | od -c | head` 看实际字节
- Windows + Python + git autocrlf + 浏览器 textarea = 4 重套娃，必须 4 重防御

### 18. bytes replace 回旋效应：双 CR 无法用 2-step replace 清理（2026-09-02 · Phase 44）

**坑**：Phase 43 用了 `replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")` 想做 CRLF 归一。**但当 input 含 `\r\r\n` 双 CR 时**：
- 第一次 `replace(b"\r\n", b"\n")`：匹配 `\r\r\n` 中的 `\r\n`（byte 2-3），剩下孤 `\r`（byte 1）
- 第二次 `replace(b"\n", b"\r\n")`：没匹配（孤 `\r` 没动），孤 `\r` 还在 → 输出 `b"\r"` 残留在每行
- **实际看到的现象**：用户保存后 textarea 显示 `的\r\n了\r\n和\r\n...` 每行带孤 CR（看不见但 `\r` 在）

**铁律**：归一化 line ending 必须**先全部归 LF**（`replace(\r\n → \n).replace(\r → \n)`），**再统一输出**（`\r\n`.join + `\r\n`）。任何"先归一再归二"的 2-step 算法都有回旋风险。

**避坑指引**：
- 写文件前的 line ending 处理：3 步算法（`\r\n → \n` → `\r → \n` → `split → filter → join(\r\n) + \r\n`）
- 不要相信 `replace(\r\n → \n).replace(\n → \r\n)` 这种"对偶"算法——它假设 input 只有 LF 或 CRLF 一种，**遇到双 CR 必坏**
- 单元测试覆盖 5 种混合 line ending（LF/CRLF/双 CR/孤 CR/混合）

---

### 19. Jinja2 `dict.key%` 中 `%` 关键字 + `}}%` 解析崩（2026-09-02 · Phase 46）

**坑**：`04_rank.html` 第一次写：
```html
<div class="metric-box"><div class="ml">加权 CTR</div>
  <div class="mv">{{ "%.2f"|format(plan_detail.加权CTR%) }}%</div></div>
```
→ Jinja2 抛 `TemplateSyntaxError: unexpected ')'`（line 43）。

**对照实验**：
- ✅ `{{ "{:,}".format(plan_detail.触达成功) }}` ← 解析 OK（无 `%`）
- ✅ `{{ summary['整体CTR%'] }}` ← 解析 OK（下标写法）
- ✅ `{{ "%.2f"|format(plan_detail['加权CTR%']) }}%` ← 解析 OK（下标写法）
- ❌ `{{ "%.2f"|format(plan_detail.加权CTR%) }}%` ← **崩**

**根因**（猜测）：Jinja2 lexer 在 `加权CTR` 后看到 `%` + `)` + `}}` + `%` 这一连串 token，**属性语法 `.key%` 与 `)` 闭合出现切分歧义**。下标语法 `['加权CTR%']` 整体作为单个 subscript token，没有歧义。

**铁律**：Jinja2 模板里 dict key 含 `%` 等特殊字符 → **永远用 `dict['key%']` 下标写法**，不要 `dict.key%` 属性语法。

**避坑指引**：
- pandas DataFrame 转 dict 后保留原列名（中文 + `%`），模板访问一律 `r['加权CTR%']`
- 不要图省事写 `r.加权CTR%` —— 看似更 Pythonic，Jinja2 解析器不答应
- 静态检查：写完模板立刻 `curl` 一次 500 → 看 uvicorn traceback 找 Jinja2 报哪一行

---

### 20. 字典 e2e smoke 必须 tmpdir 隔离，不能动真文件（2026-09-03 · Phase 47）

**坑**：Phase 47 字典维护 UI 重设做端到端 smoke 时，curl `POST /api/settings/save/channel_rules` 验证保存链路 → `_write_dict_file` 把 `config/channel_rules.yaml` 真覆盖为 `# test content from smoke 2026-09-03`（36 字节）。修复靠 `git checkout HEAD -- config/channel_rules.yaml` 还原。

**根因**：
- `_write_dict_file` 走 atomic rename（tmp + rename）但写的是**真实路径** `config/channel_rules.yaml`，不是 test fixture
- smoke 测保存链路时只想到"看 303 重定向"，没意识到这次 POST 真会落盘
- 鉴权 + 路由 + _write_dict_file 三层都没做"测试模式"开关（不像 calibrate_baseline.py 有 `--db` 参数走 tmp db）

**铁律**：
- 任何 `POST /api/*/save` / `_write_*_file` / atomic write 类端点 → e2e smoke **必须用 tmpdir 隔离**，不能让请求体落真文件
- 写新的"写文件"类工具函数时，**第一步加 dry-run / test mode 参数**（参考 `tools/calibrate_baseline.py --db` 模式），单元测试和 smoke 都能切到 tmpdir
- 不支持 dry-run 的旧端点 → smoke 用 GET 类端点验证（`/api/settings/download/{dict_id}` 返回原文件），save 链路靠 `tests/verify.py` 单元测试覆盖（Phase 44 §18 单元测试已覆盖 `_write_dict_file` 16 边界）

**避坑指引**：
- 写新文件前先问：测试能不能用 tmpdir？如果不能，**能不能加 dry-run flag？** 如果都不能，**这个端点就不能 e2e smoke，只能单元测试**
- 真要 smoke save 链路：先 `cp` 原文件到 `/tmp/orig.yaml` → smoke 完 `cp /tmp/orig.yaml config/orig.yaml` 还原（最笨但最稳）
- 不推荐"先存起来 → smoke 完恢复"模式：smoke 中途崩了无法恢复 → 还是要 git checkout 兜底

---

### 21. 性能优化"先实测再下手"——不要凭直觉猜瓶颈（2026-09-03 · Phase 48）

**坑**：用户报"从首页跳内容工坊要等一段时间才出现"，我**直觉假设**是模板编译延迟（基于"01 内容工坊模板 167 行 + 12 个 select 循环"），于是加 startup 预热，结果实测**完全无效**（startup 跑了 40.8ms 预热，GET /studio 第一次仍 2.67s）。

**根因**：
- 模板编译 + 渲染总耗时 **90ms**（实测 6 个模板 get_template 总 66ms + 第一次 render 74ms）
- 真实大头 1.3s 在 **ASGI handler 首次初始化**（uvicorn 第一次处理 HTTP）+ 业务层懒加载 import + 浏览器**全页 reload** 跳转固定开销 100-300ms
- Startup 预热对这几项**完全没有能力**触达（startup 跑的是 Python 模块内部状态，碰不到 ASGI handler / 浏览器 / 业务懒加载）

**铁律**：
- 性能优化 **不要凭"用户报 A 慢 → 应该是 X"** 猜，先 `curl -w '%{time_total}'` 测 5 次找真实耗时分布
- 找到耗时大头后，**用 Python 隔离测试**（直接调函数 + 计时）分阶段定位瓶颈所在层（模板？渲染？import？HTTP？浏览器？）
- **每一层加干预前都要有数据支撑**：startup 预热对"模板编译"是合理优化，对"首次 HTTP 慢"是无关改动
- **承认预热无效后**：保留代码无害（多 ~40ms 启动开销，价值 0），但要诚实告知用户"这次改动无效，性能优化延后"

**避坑指引**：
- 用户报"页面慢" → **第一步 curl 测 5 次**（首页 + 目标页 + 跳过的页），看耗时是均匀慢还是首次慢
- 首次慢 → **隔离测**（脱离 HTTP 直接调底层函数），看是 ① 模块 import ② 模板编译 ③ 渲染 ④ 业务计算 ⑤ 数据库哪段
- 每一段加代码后 → **再 curl 5 次**对比耗时，找不到收益的改动保留无害但要标注"无效"
- 涉及 startup / on_event 类的"启动期优化" → 几乎只能解决 **Python 字节码缓存 + 模块预热**，不能解决 ASGI / 浏览器 / 业务懒加载

**对照实验数据**（Phase 48 实测）：
- `curl GET /studio` 第 1 次 1.33s，第 2-5 次稳定 2ms → 确认"首次慢"
- Python 直接 `templates.env.get_template('pages/01_内容工坊.html')` 18ms → 模板不是大头
- Python 直接 `_01_context() + render()` 完整 74ms → 渲染不是大头
- 90ms（模板 + 渲染）vs 1.33s（HTTP）→ 差 1.24s 是 ASGI / HTTP / 浏览器开销

---

## 已删（详见 git log 早期 commit / memory）

| 类别 | 删节项 |
|---|---|
| setup_and_run.bat 闪退 | v1-v5 各版详细失败原因 |
| analyzer → text_analyzer 脱 Streamlit | @st.cache_data → lru_cache / frozenset 替代 set 的细节 |
| 小 bug | diagnose_problems 参数陷阱 / Candidate.id=A/B/C 校验 / Candidate.title 允许为空 / CTR Adapter _demo_pred bl=None 兜底 / verify.py CSV bytes literal 限制 |
| 工具 | PowerShell 编码（WriteAllText+UTF8Encoding($false)）/ OneDrive + git 恢复（按 memory `feedback-onedrive-git`）/ github 推送（直连 github.com，分叉用 `--force-with-lease`）/ Python 字符串嵌套双引号（用中文「」替） |
| 极简 yaml 解析 | 行内 # 注释陷阱——已被第 4 条 PyYAML 替覆盖 |
| 决策文档驱动开发 | 接活前 grep `/c/Users/a952462/Downloads/` 找决策 md（已写入 Handoff.md §9 新 Session 第一步） |
| verify.py 用例数演进 | 82→152→...→854（简化为 Handoff.md §6.0 速查） |
