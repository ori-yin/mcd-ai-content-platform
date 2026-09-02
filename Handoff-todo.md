# mcd-ai-content-platform — 待办与候选（详）

> **何时读我**：开新 Phase 前扫这里，看哪些待办可顺手清掉 / 哪些候选已被否决。
> 索引在 `Handoff.md` §6.2/§6.3 + 本文件目录。

---

## 目录

- [§6.2 待业务确认（按返工风险梯队）](#62-待业务确认按返工风险梯队)
- [§6.3 候选（详 §5.5 CTR Roadmap）](#63-候选详-55-ctr-roadmap)
- [§6.4 技术债 backlog（不上线不修）](#64-技术债-backlog-不上线不修)

---

## 6.2 待业务确认（按返工风险梯队）### 6.2 待业务确认（按返工风险梯队）

> 防返工背景见 `Downloads\Demo范围决策与待确认_2026-08-26.md`。**拍板前不动后端反哺 / 不启用灰态字段**。

**第一梯队（高返工 · 现在就该确认）**
- [x] **#5** CTR **口径定义**（哪个 CTR / 去重规则）—— ✅ Phase 6 P2 已拍板，详 `docs/ctr-kpi-definition-proposal-v0.2.md`
- [x] **#6** 反哺是否**影响生成排序**（A/B/C 候选排序）—— ✅ Phase 7.2 拍板：同意，rank_candidates_by_ctr 已实现（pred_ctr 降序 + title 长度兜底）
- [x] **#3** CTR 反哺**触发条件**（累计多少 plan / 定时？）—— ✅ Phase 7.1 拍板：每周一上午手动跑一次，详 `docs/ctr-feedback-schedule.md`

**第二梯队（中低返工 · 可后置）**
- [x] **#1** 产品与权益 维度枚举 + 是否参与生成 —— ✅ **Phase 9 已拍板**，详 `Downloads/decision-product-benefit-2026-08-26.md`（拆 `product_category` + `benefit_type` 两字段；10 产品 + 8 权益枚举 +「自定义」输入兜底；必填 + 参与生成；jieba 词典与 yaml 枚举解耦并行）
- [x] **#2** 投放目标 维度枚举 + 是否参与生成 —— ✅ **Phase 9 已拍板**，详 `Downloads/decision-objective-2026-08-26.md`（6 值 → 4 值收敛：品牌认知 / 点击驱动 / 转化促成 / 用户召回；**支持多选，逗号分隔，max 3，union 合并**；必填 + 参与生成 + 影响 strategy+tone，不约束 product；baseline 新增 objective_x_渠道 = 90 key，7 级回退兜底）
- [x] **#4** CTR 校准频率 —— ✅ **用户拍板（2026-08-31）**：从 Phase 7.1「每周一上午手动」改为**每月一次手动**（建议每月 1 号上午跑）。`tools/weekly_calibrate.bat` 仍落档不调度，月初手动执行；`docs/ctr-feedback-schedule.md` 频率段待同步修订
- [x] **#7** 02-05 附属页面 + 字典维护 UI 纳入正式版 —— ✅ **用户拍板（2026-08-31）**：UI 重设阶段一起做（首页 00 入口重排 + 字典 UI 独立页 `pages/06_settings.py`）。02 单条诊断 / 03 批量评估 / 04 七 Tab 洞察 / 05 上传回流 + 06 字典维护全部进正式版
- [x] **#7a** UI 重设计落地（FastAPI + Jinja2 + HTMX 全量迁移，§62 · 2026-09-01） —— ✅ **Phase 26 完成**：5/5 页面已从 Streamlit 迁到 `web/templates/pages/` + 13 API + 金拱 SVG 替换 M 字母 + 居中 primary button + LLM 状态 pill；旧 Streamlit `pages/0X_*.py` 保留作 fallback。**字典维护 UI（`pages/06_settings.py`）仍待 Phase 27+**——本次迁移范围只覆盖 00-05。

**第三梯队（用户口径 · Phase 10 拍板稿 · 2026-08-27 用户会话提）**

> 用户视角：维度设计需贴近业务实际，不是 form 字段堆积。**核心观点**：CTR 真实影响因子在**文案内容**（标题/正文是否带券、含场景关键词）而不是 form 字段值；投放日期影响系数靠工作日类型推算，不需要具体日期。

#### 已拍板（已落地 Phase 11 · 2026-08-27）

- [x] **#12 工作日/非工作日 2 值（用户简化拍板 2026-08-27 · Phase 11 已落地）**
  - **原始拍板稿是 3 值（法定节假日/非工作日/工作日），用户当天简化成 2 值**——不要日期选择器，法定节假日暂不做
  - 替换 date_input → selectbox 二选一：**工作日 / 非工作日**
  - 默认值按今天自动算（`classify_today_type()` 走 weekday 逻辑，周一~周五=工作日，周六周日=非工作日）
  - baseline JSON **不动**——现有 "渠道_x_工作日类型" 2 值 key（`data/ctr_baseline.json:135-146`）正好对齐，无需新增 3 值维度
  - 落地文件：
    - `core/data_window.py` 加 `classify_date_type(target) → "工作日"|"非工作日"` + `classify_today_type()` 工具函数（纯 weekday 逻辑，不依赖节假日字典）
    - `pages/01_content_studio.py:189` date_input → selectbox 2 值；默认按今日自动算
    - `core/schemas.py:187` `TaskInput.planned_send_date` 字段名保留（孤儿字段，下游 0 消费），注释更新为"工作日/非工作日 标签"
    - `tests/verify.py §45` 加 18 个用例（5 工作日 + 2 非工作日 + 3 输入类型 + 3 边界 + 3 跨年 + 1 today 合法 + 1 错误抛错）
  - 法定节假日 / 调休 暂不支持；baseline_lookup.py 现有 2 值 key 仍按"工作日/非工作日"统计（节假日日期会被算进"非工作日"）

#### 已落地（Phase 12 · 2026-08-27 · 用户喂 CNN0827 数据后一拍板）

- [x] **#8 渠道枚举清洗 + 对齐** —— 用户拍板："公众号推文删除"
  - 清洗脚本 `tools/clean_cnn_backup.py` 滤掉"无需渠道"(434) + "微信公众号推文"(19)，输出 `data/cnn_backup_cleaned.xlsx`（48307 行 / 3821 plan / 4 渠道）
  - baseline JSON v3.1 → **v3.1.1**：删 14 个 key（微信公众号推文 12 维度 + 微信订阅 2 维度 + optimal_chars 2 项）
  - schema `CHANNELS` 删"站内信" + 加"微信小程序订阅消息" + "企微 1v1" → "企微1v1"（跟数据源连写）；最终 4 渠道：`APP Push / 企微1v1 / 短信 / 微信小程序订阅消息`
- [x] **#9 Plan 命名统一** —— 用户拍板："按我的数据源来"
  - schema `PLAN_TYPES` 改 `("AARRPlan", "常规Plan", "未知")`（连写，跟数据一致）
  - baseline_lookup.py:76 顺手修 bug：原 `("AARRPlan", "普通Plan")` → 修 `("AARRPlan", "常规Plan")`（baseline JSON 实际用"常规Plan"，导致 *_常规Plan key 从未命中过；v3.0 → v3.1 一直有这个 bug）
- [x] **#10 场景字段改选填 + 内容推断** —— 用户拍板："必填改选填呗"
  - `TaskInput.REQUIRED_FIELDS` 从 5 → 4（去掉 scene）；scene 字段挪到 has-default 区（dataclass 字段顺序铁律）
  - 内容推断工具函数（`classify_scene_in_text`）**未做**——等用户喂场景关键词词典（`config/scene_keywords.yaml`）后再实现；baseline 新增"渠道_x_文案场景"维度同理等数据
- [x] **#11 用券双字段保留** —— 用户拍板："保留 form 字段，但是不是要加两个"
  - **用户假设反转**：CNN0827 数据验证 form "实际是否用券"才是主驱动（企微 1v1 form 用券 2.56x vs 文案含券 1.32x；APP Push 文案含券反向 0.84x）；用户拍板保留 form 字段
  - 新增第二个字段 `text_has_coupon: str = ""`（标题正文是否带券，由 `classify_coupon_in_text(title, body)` 推断）
  - `core/text_classifier.py` + `config/coupon_keywords.yaml` v1.0（discount/coupon/link 三类；删 `\d+元` 太宽）
  - `pages/01_content_studio.py` 加 selectbox；已有 coupon label 改"实际是否用券"
  - baseline_lookup.py 新增 `text_has_coupon` 参数 + "渠道_x_文案含券词" 维度分支（baseline JSON 暂无 key 走兜底；等用户重算 baseline）

#### Schema 兜底字段决策（Phase 12 · 2026-08-27 · 用户拍板）

- [x] **PLAN_TYPES / COUPON_FLAGS 保留"未知"** —— schema 兜底字段，非数据源枚举
  - 数据源枚举：计划类型只 2 值（AARRPlan 93.3% + 常规Plan 6.7%，distinct=2）；是否用券只 2 值（是 67.2% + 否 32.8%，distinct=2）
  - "未知"在 baseline_lookup 里的实际行为：`baseline_lookup.py:86` 接受 `("是", "否")` → "未知" 跳过 `渠道_x_是否用券` 维度分支 → 走 `渠道整体` 兜底（**粗粒度 fallback，不是 0 系数**）
  - 不删"未知"原因：form 字段不填时需要 UI 兜底；删了强制 form 必填损失 UX 防御性
- [x] **指数平滑衰减已实现** —— baseline JSON `calibration_lambda=0.01 / half_life_days=69.3 / weighted_method=exponential_decay`（`data/ctr_baseline.json:8-12`），所有维度 CTR 都是加权后的（越靠近 `last_updated` 权重越高，半衰期 69.3 天；2024-10 老数据权重 ≈ 0.0014）
- [x] **用券细分维度暂不做** —— 业务侧 form "是否" 已确认是主驱动（#11 反转）；数据列无结构化"用券类型"字段；关键词推断 ROI 不明确；等跑一阵 #11 双字段数据后看 CTR 离散度再决定

#### 已确认无需动

- [x] **#13 指数衰减（EMA）已实现** —— baseline JSON（`data/ctr_baseline.json:8-12`）已含 `calibration_lambda=0.01 / half_life_days=69.3 / weighted_method=exponential_decay`；`_note` 写"越靠近 2026-08-16 的数据权重越高"

#### 第三梯队 · 下次迭代目标

- 用户口径：**下次 session 喂数据 → 写入具体阈值**
- 落地路径：①用户给数据（Plan × CTR × 触达）→ ②按第三梯队已拍板项对齐 schema/baseline → ③`pages/05_feedback` 上传 / 直接走 `tools/calibrate_baseline.py --db data/feedback.db` → ④重算 `data/ctr_baseline.json` → ⑤下次 demo/真实预测就用新值
- 已落地前置：#12 工作日/非工作日 2 值（Phase 11）

### 6.3 候选（详 §5.5 CTR Roadmap）

> **业务确认后启动**（下方 P4 仍待启动；UI 重设计 §62 已落地 → 见 Phase 26；L1 已落地 → docs/l1-training-runbook.md）。

#### L1 · LightGBM 回归替 baseline 查找表 ✅ 已落地

- Phase 18 PoC + Phase 19 入生产 + Phase 20 l1_model mode + Phase 22 B/C/D 闭环 + Phase 24 sweep 确认 live
- **业务拍板 4 项全部 ✅**（2026-08-31）：切 L1 时点 = 用户主动 / 训练责任人 = 用户自己 / 误差告警阈值 = baseline × 1.3 / 可解释输出 = 月报 + 用户自看
- **训练 / 监控 / 漂移处理 / 回退 / 月报 5 步流程**见 `docs/l1-training-runbook.md`
- **回退机制基本闭环**：Phase 22 C 已落 `core/active_mode.py` + monitor_l1_drift.py:apply_auto_rollback（drift → 写 active_mode.txt → 01 启动读 + 黄 banner）

#### L1 详档

- 业务拍板 4 项历史拍板稿 + Phase 18 PoC 设计稿（GBDT vs DNN / 特征工程 / 样本阈值）已合并到 `Handoff-decisions.md` §5.5 CTR Roadmap（**Roadmap 摘要 + 拍板记录**）

---

#### P4 · 历史洞察签名关联（候选 · 2026-08-31 延后到 UI 重设一起做）

**一句话**：04 第 8 Tab 加 signature 视角，让业务闭环"看"反哺（采纳数 / 预测 CTR 平均 / 真实 CTR 中位数 / 预测 vs 真实 diff）。

**2026-08-31 拍板延后**：P4 跟 UI 重设阶段一起做，避免改两次 04 页面结构（当前 P4 候选 + UI 重设都要动 04）。

**业务要拍 4 项**（UI 重设启动时确认）：
1. **要不要加** → ✅ 用户已确认（"P4 现在可以做到了吗？就是 CTR 预测 + feedback 对吧"）
2. **CTR 列显示阈值**：建议 ≥ 5（feedback 样本 ≥ 5 才显示真实 CTR 列）
3. **展示粒度**：建议 signature 12 位（细 12 位指纹）+ 可展开看 strategy
4. **与 L1 联动**：先有"看"再有"用"，P4 数据正好是 L1 训练数据

**数据基础已就绪**（Phase 5 P0/P1/P2）：records.signature ↔ feedback.task_signature 可 join；signature_insight_service 预估 ~100 行 + pages/04 加第 8 Tab。

**前提**：feedback.db 当前 0 行 → 真实反馈回灌前 CTR 列会全空（P4 Tab 加了先看"采纳数"维度）。

---

#### UI · 整体重设计（候选 · 2026-08-31 延后，最后做）

**用户反馈（2026-08-28）**：核心逻辑已完成，**UI 太丑，整体架构 + 布局都有大问题**。下一步计划整体重构，不是修修补补。

**2026-08-31 拍板 → 2026-09-01 落地**：UI 重设大部分做（Phase 26 5/5 页面 + 13 API 落地，见 Handoff.md §6.1）；**P4 + 字典维护 UI（`pages/06_settings.py`）仍待二轮 UI 优化（Phase 27+）**，避免改 04 页面结构两次。

**find-skills 调研结论**（2026-08-28）：

**已装可直接用**（`~\.claude\skills\`）：
- `developing-with-streamlit` —— **最对口**，Streamlit 官方
- `frontend-design` / `designing-beautiful-websites` —— 通用

**skills.sh 高命中**（待评估装不装）：
| Skill | installs | 备注 |
|---|---|---|
| `vercel-labs/agent-skills@web-design-guidelines` | **58.4 万** ⭐ | 通用 web 设计准则 |
| `nextlevelbuilder/ui-ux-pro-max-skill@ckm:design-system` | 3.3 万 | UI/UX 设计系统 |

**下一步行动**（启动时）：
1. 跑 `developing-with-streamlit/scripts/discover.py` 拿项目级 recommendations
2. 按输出决定补装外部 skill
3. 走 skill 流水线整体重构（CLAUDE.md §9 红线）
4. 同步做 P4 第 8 Tab + 字典维护 UI + 02-05 正式版统一（**2026-09-01 注解**：02-05 页面已迁完正式版 UI，剩 P4 第 8 Tab + 字典维护 UI 待 Phase 27+）

**作用域**：6 页面（app + 00-05）+ banner 系统 + sidebar 主题；**不动后端逻辑**。

---

## 6.4 技术债 backlog（不上线不修）

> **原则**：严格遵守 CLAUDE.md §9 + UI 重设不动后端。当前 3 条，不写实现细节，保持精简。触发时机到来时再清，不让 backlog 长成"完整工程治理清单"。

| # | 债项 | 触发时机 |
|---|------|---------|
| P1 | `feedback_lookup.py` 破窗焊死：加单测断言"无其他 adapter import sqlite3" | 任意对外分享前（含临时演示） |
| P2 | 清 orphan field：`planned_send_date`（删前 grep 确认无人读，再从 TaskInput 移除） | 任意动 TaskInput 字段前（不只是上线） |
| P2 | 补 10 处弱断言（`_check(x, True)` → 断言值正确） | 任意一轮重构或弱断言自然碰到时 |

**为什么现在一律不动**：
- 动 TaskInput 字段顺序 = 踩 dataclass 铁律 + 改 854 用例
- 动 feedback_lookup.py 破窗 = 改 adapter 接口，UI 重设阶段不允许动后端
- 补弱断言 = 数值固定化会绑死重构空间

**配套防腐烂**：每次新建会话先扫本表，已完成项打 ✅ + 移出表。

---

## 6.5 Phase 38 A1-mid 同步条目（2026-09-01）

**已完成**（Phase 38 A1-mid · commit fd94aea + 816eb85）：
- ✅ §6.2 #7a UI 重设落地 → 已完成（5/5 页面 + 13 API + 金拱 SVG），本轮 A1-mid 是 UI 统一收尾
- ✅ §6.4 技术债 P1/P2/P2 仍未动（UI 收尾阶段不允许动后端）

**新增洞察**（design.md §12）：
- ⚠️ Handoff 数字漂移是「schema 改 → verify.py 同步改」铁律失效的体现（详见 design.md §12.1）
- ⚠️ inline 收敛暴露设计系统漏洞的根因 = design.md §2.6 / §2.8 没把变体列全（详见 design.md §12.2）
- ⚠️ design.md 缺 DNA 段 = 「4 条铁律」表无法给新 session 提供哲学锚点（详见 design.md §12.3）

## 6.6 Phase 40-43 字典维护鉴权 + 3 个连环 BUG 修复（2026-09-02）

**已完成**（Phase 40-43 · commit d6417c9，远端 32508fb3bd62）：
- ✅ 字典维护鉴权（Phase 40）：左侧栏隐藏 + 密码 `ori1026` 鉴权 + cookie `path=/` 修复
- ✅ stopwords 字典（Phase 41）：产品词典加 stopwords 字段，jieba 热重载
- ✅ textarea 双重 escape 修复（Phase 41-42）：tojson + `<script type="application/json">` 避开 HTML attribute `\n` 截断
- ✅ 双 CR BUG 修复（Phase 43）：custom_dict.txt 清空 `\r\r\n` + 空行（135→68 行），`.gitattributes` 防御，`_write_dict_file` bytes CRLF 统一

**新增洞察**：
- ⚠️ Jinja autoescape + `| e` 双 escape 是 textarea 的高频坑（textarea 不解析 entity）
- ⚠️ HTML5 attribute `\n` 截断 spec 坑：多行数据绝不放 attribute
- ⚠️ Cookie path 严格匹配 + `/api/*` 是兄弟路径 = 必须 `path=/`
- ⚠️ Windows + Python + git autocrlf + 浏览器 textarea = 4 重 line ending 套娃，必须 4 重防御

**验证**：848 PASS / 0 FAIL（无回归）+ smoke 7 case 全过。

**TODO 后续**（不属于本轮）：
- ⏳ 字典维护 UI 重设（按 Phase 37 design.md 路线图收尾）
- ⏳ L2 模型训练数据准备（领导口径「输入因子有效性检查 vs 第一版 base」差距分析待落地）

## 6.7 Phase 44 _write_dict_file 4 重防御（2026-09-02）

**已完成**（Phase 44 · commit 3ba20c5，远端 956ec3b64cd8）：
- ✅ _write_dict_file 4 重防御：CRLF/孤 CR 归一 LF → 过滤空行 → rstrip → 输出 CRLF
- ✅ 单元测试 16/16 PASS（tmp_normalize_test.py 覆盖 5 种 line ending 混合 + 中文）
- ✅ smoke e2e：注入 `\r\r\n` 双 CR + 空行后保存，输出干净（0 双 CR / 0 空行）
- ✅ 顺手修 push 脚本 archive 嵌套 ROOT 路径（§13 教训复现）

**新增洞察**：
- ⚠️ `replace(\r\n → \n).replace(\n → \r\n)` 有**回旋效应**——遇到双 CR 必坏（详见 lessons §18）
- ⚠️ bytes replace 必须先用 `.replace(b"\r\n", b"\n").replace(b"\r", b"\n")` 归一，再统一输出
- ⚠️ 用户试探"换表格"方案——4 重防御已经能防住所有 line ending 边界，表格方案作为备选留待后续

**TODO 后续**：
- ⏳ 字典维护 UI 重设（按 Phase 37 design.md 路线图收尾）
- ⏳ 表格方案备选（如果 4 重防御后还出问题再考虑）

## 6.8 Phase 45 字典本地备份（2026-09-02）

**已完成**（Phase 45 · 2 commits）：
- ✅ **Commit 1** `8d09f71`（远端 `6a7ad524869c`）：CLI 脚本 + 双击 .bat + .gitignore
- ✅ **Commit 2** `4c032a6`（远端 `51ed42480e56`）：web settings_save 自动触发 + 每天首次去重

**用户反馈路径**：用户原话"应该是我明白次保存"——理解成"每次保存自动备份"，不是定时 cron。

**设计要点**：
- ✅ 7 个字典文件全备份（custom_dict/stopwords/ctr_baseline/4 个 yaml）
- ✅ tar.gz 压缩（19KB → 7KB）
- ✅ 每天首次保存才创建（同天去重，避免产生垃圾）
- ✅ 保留 14 天自动清理
- ✅ `data/.backups/` 已 .gitignore（不污染 git）
- ✅ 备份失败 try/except 兜底，不阻塞保存
- ✅ 双重保险：本地 tar.gz + 远端 git 历史

**flash 文案反馈**：
- 首次：「产品词典 保存成功 · 已自动备份 7 个字典文件 (19,309 字节)」
- 重复：「产品词典 保存成功 · 今天已备份过（dicts_2026-09-02_153217.tar.gz），跳过」

**TODO 后续**（不属于本轮）：
- ⏳ 字典维护 UI 重设（按 Phase 37 design.md 路线图收尾）

---

## 6.9 Phase 46 历史洞察 4 BUG 修复 + 3 Tab 查询增强（2026-09-02）

**已完成**（Phase 46 · 1 commit 待 push）：
- ✅ **BUG 1**：daily 500（pandas `round()` 不接受 pd.NA） → 改 `astype("Float64")` nullable 类型
- ✅ **BUG 2**：wf 选词对比 select → input（form-row-span2 占 2 列 + CSS 缓存 `?v=20260902wf`）
- ✅ **BUG 3**：6 个 tab form 加 `<input type="hidden" name="tab" value="X" />`（rank/wf/ef/sim/owner/daily），提交不再跳回 rank
- ✅ **BUG 4**：wf 单词对比位置重排（表单 → 单词对比 → 高效词 → 低效词），自然无跳动
- ✅ **增强 1**：rank Tab "输入 Plan ID 查详情" → 新 `_plan_detail()` helper + 详情区块（紧贴表单）
- ✅ **增强 2**：ef Tab "输入 emoji 查对比" → 复用 `compare_token(col=_emojis)` + 对比区块（紧贴表单）

**踩坑教训**（Handoff-lessons.md §19）：Jinja2 模板 dict key 含 `%` → 永远用 `dict['key%']` 下标写法，不要 `dict.key%` 属性语法（解析器崩 `unexpected ')'`）。

**验证**：5 GET endpoints + 5 form 提交 → 全 200；`tests/verify.py` 848 PASS / 0 FAIL。

**不动**：
- ⏳ 其他 insights tab 增强（如 sim topk UI 微调等）暂不展开（本轮聚焦 daily/wf/rank/ef）
- ⏳ 按钮/handler 全量 smoke 发现无其他 BUG，留作下一轮被动发现

---

