# mcd-ai-content-platform — 决策记录（详）

> **何时读我**：新 session 想了解"为什么 Phase X 这样设计"时，按 Phase 编号搜这里。
> 速查表在 `Handoff.md §6.1`。
> **本文件已压缩**（2026-08-31）：Phase 1-10 早期决策压成 1-2 行 + 1-2 句 why；Phase 11+ 保留详细。删 git commit message 已经有的细节。

---

## 5. 决策记录

### 2026-08-24 · 项目立项 + Phase 1-3.2

- **项目立项**：PRD v2.0 + 3 处补充（§4.0 CTR 三入口 / §13.5 Adapter 策略 / §15.A 工程化配套）。why：单页面 mcd-copy-analyzer 不够用，统一整合到内网工作台
- **端口 8510**：避让 mcd-copy-analyzer 8501
- **setup_and_run.bat 闪退 5 次迭代**：最终 v5 跳过 venv，用系统 Python。why：venv 在 Win11 子系统下不可靠
- **bat 文件必须 CRLF**：cmd 严格要 CRLF，Write 工具默认 LF。why：v5 闪退第 6 次才发现 LF
- **Phase 1**：CTR Adapter 4 模块（baseline/prompt/column/char）+ `PredictionResult` dataclass；verify 82 PASS
- **Phase 2**：抽 copy-analyzer Adapter + 6 模块；verify 152 PASS
- **Phase 3**：6 service + 2 prompt + 1 repository + 2 yaml + 5 页面占位；st.Page("app.py") 自引用递归 bug 修复；verify 230 PASS

### 2026-08-26 · Phase 4 业务页 + CTR Adapter bug

- **Phase 4**：pages/02/03/04 三业务页落地（单条诊断/批量评估/七 Tab 洞察）；01 渠道预览升级到高保真；verify 290 PASS
- **CTR Adapter bug 修复**：`_demo_pred` 在 `_bl_str="未知"` 时 bl*100 抛 TypeError，新增 bl=None 兜底；predict_one 重写不走 Candidate 包装

### 2026-08-26 · Phase 5 CTR 反哺闭环 P0+P1+P2

- **P0 record 指纹**：task_signature SHA1-12（channel/coupon/plan_type/audience/stage/scene + 标题/正文桶）。why：让 records.db ↔ feedback.db 可 join
- **P1 feedback 库**：repositories/feedback_repository（SQLite）+ pages/05_feedback 上传
- **P2 baseline 校准自动化**：calibrate_baseline.py 三段策略（<5 跳过 / 5-20 EMA α=0.3 / ≥20 全量）。why：手动 EMA 容易漂移，自动三段防过拟合
- **GitHub secret scanning**：tools/push_via_api.py 硬编码 token 被扫描阻断，改读环境变量

### 2026-08-26 · Phase 6 P0 业务确认 + 企微 1v1 预览 + LLM 留空

- **业务确认 12 项**（详 docs/architecture.md §五）：Demo 主渠道 APP Push + 企微 1v1；枚举/字数/词表复用 yaml；predictor 走 main 版；内网 LLM 暂留空
- **企微 1v1 聊天气泡**：ui/styles.py 加 `.wechat-bubble-wrap` + 01 替换占位
- **LLM 留空 banner**：config/llm_settings.yaml 4 字段全空 + ui/llm_status.py 检测器 + `.llm-warning` 样式。why：未配置 LLM 时给用户清晰提示
- verify 349 PASS

### 2026-08-26 · Phase 6 P1 灰态 + 进阶弱化 + CTR 免责

- **决策 1（6 维度前端灰态）**：product_benefit/objective 改 disabled=True + label 加「待开发·二期接入」+ help tooltip。why：拍板前不接后端，避免半成品数据污染
- **决策 2（4 附属页面弱化）**：advanced_notice banner + 首页分组卡（核心大/进阶小）。why：避免业务方误以为 02-05 已正式
- **决策 3（CTR 反哺免责）**：04/05 顶部 banner "演示口径·业务确认前不接真实数据"。why：保护合规边界
- **不动**：app.py / 后端反哺 / 任何页面删除
- verify 395 PASS

### 2026-08-26 · Phase 6 P2 CTR 口径固化 v3.1

- **Q1-Q6 拍板**：Q1 去重点击 / Q2 触达成功 / Q3 全周期 / Q4 不跨渠道 / Q5 min_reach≥1000 / Q6 业务确认前不接真实
- **bi_dt 铁律**：12 点前 T-2 兜底，新增 `core/data_window.resolve_bi_dt_window()`
- **6 文件落地**：baseline JSON v3.1 + 5 处注释同步 + docs/ctr-kpi-definition-proposal-v0.2.md 拍板稿
- **关键前提**：导出表口径必须与 Q1-Q6 完全一致，否则"真实值"是另一套定义
- verify 421 PASS

### 2026-08-26 · Phase 6 P3 simplify 清理

- **修 A 手写 yaml → yaml.safe_load**：ui/llm_status.py 30 行 → 1 行（PyYAML 已依赖）
- **修 B 4 处 v3.1 docstring 缩成 1 行**：ground truth 只留 baseline JSON
- **修 C 删 PENDING_FIELDS 死元组**
- **修 D 删 core/data_window.py _to_local aware datetime 死分支**
- **修 E ui/notice.py 抽 render_notice helper**
- 净减 56 行

### 2026-08-26 · Phase 7 业务拍板落地 #3 + #6

- **#3 触发条件**：每周一上午手动跑 calibrate_baseline.py → 新文档 docs/ctr-feedback-schedule.md（**2026-08-31 用户改月度**）
- **#6 反哺影响排序**：rank_candidates_by_ctr 纯函数（pred_ctr 降序 + title 长度兜底）+ 默认 selected_id 改最 CTR 那条
- **顺手清理**：删 phase6_p1/p2_push.py 临时文件

### 2026-08-26 · Phase 8 pytest 迁移 + Phase 6 P4 候选扫除

- **pytest 迁移**：verify.py 加 `_RUNNING_UNDER_PYTEST` 标志 + pytest.ini + 双路一致（CLI 428 + pytest 43）
- **P3 维度权重动态**：config/dimension_weights.yaml + tools/train_dimension_weights.py（v0.1 占位）+ text_analyzer.diagnose_score 加权聚合
- **demo 数据回灌**：feedback_lookup.py（FEEDBACK_READY_MIN_PLANS=50 + lookup_feedback_ctr by signature）。why：让 01 demo mode 在有真实数据时显示真实 CTR 而非 baseline × tm 兜底
- **铁律**：adapter 直接 sqlite3，不 import repository（CLAUDE.md §4.1）

### 2026-08-27 · Phase 9 #1/#2 业务拍板（盲点修正）

- **#1 产品与权益**：单字段 product_benefit → 拆 product_category + benefit_type；10 产品 + 8 权益 +「自定义」兜底；必填 + 参与生成 + jieba 词典与 yaml 枚举解耦并行
- **#2 投放目标**：PRD 6 值 → 4 值（品牌认知/点击驱动/转化促成/用户召回）；**多选**（逗号分隔 max 3，union 合并）；必填 + 参与生成 + 影响 strategy+tone
- **修正 1**：baseline_lookup 实际是 7 维 ≠ Handoff §2 写"7 维含 objective"，objective 是新增维度（7→8，不是 6→4 收敛）
- **修正 2（盲点）**：用户 Q1（新品+大促）+ Q2（召回+新品推荐）都是多目标并存 → 改多选 → baseline 24 → 90 key（2^4-1 × 6，7 级回退）。why：单选会强迫业务方简化信息
- **暂搁**：字典维护 UI pages/06_settings.py（**2026-08-31 用户拍板纳入正式版，跟 UI 重设一起做**）

### 2026-08-27 · Phase 11 #12 工作日 2 值简化

- **用户拍板反转**：原 3 值（法定节假日/非工作日/工作日，需节假日字典）→ 2 值（**只 selectbox 工作日/非工作日**）。why：节假日字典维护成本高，先做最小可用版本
- **实现**：classify_date_type / classify_today_type 纯 weekday 函数（不依赖节假日字典、不处理调休）；baseline JSON 现有 2 值 key 正好对齐
- **后续扩展路径**：要支持节假日时建 data/holidays.yaml + 3 值 baseline key
- verify 491 PASS

### 2026-08-27 · Phase 12 schema 兜底字段 + #8/#9/#10/#11 落地

- **PLAN_TYPES/COUPON_FLAGS 保留"未知"**：schema 兜底（form 不填时 UI 防御），不是数据源枚举（实际只有 2 值）。"未知" ≠ 0 系数（baseline_lookup 跳过该维度分支，走渠道整体兜底）
- **指数平滑衰减已实现**：baseline JSON v3.0+，λ=0.01 半衰期 69.3 天（越靠近 last_updated 权重越高）
- **#11 用户假设反转**：用户原假设"文案带券词影响更大"，CNN0827 数据验证反转 → form "实际是否用券"才是主驱动（企微 1v1 2.56x vs 文案含券 1.32x；APP Push 文案含券反向 0.84x）。**保留 form + 新增 text_has_coupon 双字段**
- **#8 渠道清洗**：删除"无需渠道"(434) + "微信公众号推文"(19)；baseline v3.1.1 删 14 个 key；schema CHANNELS 加"微信小程序订阅消息" + "企微 1v1"连写
- **#9 Plan 命名统一**：PLAN_TYPES 改 ("AARRPlan", "常规Plan", "未知")（连写）；baseline_lookup.py:76 顺手修"普通Plan"→"常规Plan" bug（v3.0 → v3.1 一直存在）
- **#10 SCENES 改选填**：REQUIRED_FIELDS 5 → 4；scene 字段挪到 has-default 区
- verify 522 PASS

### 2026-08-27 · Phase 13 工具定位重定义

- **用户口径**：CTR 评估是辅助决策工具，不是选文案工作流 → 业务方看 3 候选 + CTR 估计 → 自己决定 → 不入库
- **3 按钮全砍**：编辑候选 / 恢复 AI 原文 / 保存当前选择（无人用文案 + records.db 是死数据）
- **records.db 保留但 UI 不调用**：未来 train_dimension_weights.py 可能读 records.db 关联 feedback.db；UI 不暴露"保存"入口，业务方不点击 → 不增长
- **Candidate 字段重构**：删 title_edited/body_edited + effective_title/body/is_edited/reset_edit；引用方 4 文件改 effective_* → title/body
- verify 525 PASS

### 2026-08-27 · Phase 14 + 15 row key 修复 + baseline v3.2

- **用户报告**："选了具体指标 CTR 没变" → 排查发现 2 类根因：
  1. row key 不匹配：_candidate_to_row 输出英文 key，prompt_builder 读中文 key（plan_type/coupon/owner 3 字段读不到）
  2. workday 孤儿字段：TaskInput.planned_send_date 下游 0 消费
- **修复**：_candidate_to_row 中英文 key 双输出 + workday 透传 + prompt_builder.py:101 "普通Plan"→"常规Plan"
- **新增维度**：tools/recalc_text_has_coupon.py 从 cnn_backup_cleaned.xlsx（48307 行）按指数衰减 λ=0.01 聚合 8 keys → baseline v3.2
- **关键发现**：文案含券词对 CTR 渠道差异极大（APP Push 反向 0.84x，企微 1v1 / 微信小程序 / 短信 1.32x / 1.05x / 2.77x）→ 印证 #11 用户假设反转
- verify 557 PASS

### 2026-08-28 · Phase 16-17 代码质量清理

- **Phase 16 calibrate_baseline 扩 2 维度**：text_has_coupon + workday；feedback_repository 加 text_has_coupon 列 + ALTER 兼容老库
- **Phase 16.5 上线声明**：用户拍板"先上线再说"——weekly_calibrate.bat 仅落档不调度；L1 模型升级延期待样本 ≥ 1000
- **Phase 17 多项清理**：02 页面 bug / LLM call LRU cache / weighted_ctr 合并 / 死代码删除 / CSV reader 合并 / rule_engine 重构 / jieba 批量向量化 / Streamlit 页面缓存

### 2026-08-28 · Phase 18 L1 LightGBM PoC

- **用户拍板"先试试看"**：基于 cnn_backup_cleaned.xlsx 4.4 万行训练
- **关键决策**：
  - 剔除微信小程序订阅消息（仅 7 Plan，统一模型被带偏）
  - 特征 14→15 维（5 数值 + 6 类别 one-hot + 1 高效词命中 + 1 计划类型 TE + 1 工作日）
  - 时间衰减权重 half_life=180 天
- **结果**（baseline v3.2 同口径 evaluate_lgbm.py 复现）：L1 MAE 0.395%（vs L0 0.416% 同口径降 5.2%），R² 0.0824（vs L0 0.0659）
- **3 渠道 L1 全胜**：APP Push 0.273% / 企微1v1 0.682% / 短信 0.203%
- **关键发现**：渠道×工作日交叉特征为负向（LightGBM 自己能学，显式加 = 特征冗余）

### 2026-08-28 · Phase 19+20 L1 入生产 + 漂移监控

- **Phase 19 静默双轨**：l1_predictor.py（predict_l1/predict_l1_batch/predict_l1_status）+ sidebar admin checkbox 默认关；模型缺失/渠道不在训练范围时静默降级 unavailable，主流程不受影响
- **Phase 20 l1_model mode 主流程接入**：CTRPredictionAdapter.VALID_MODES 加 "l1_model"（5 态）+ sidebar selectbox（demo/baseline_only/l1_model）+ L1 模型缺失时不可选
- **漂移监控**：tools/monitor_l1_drift.py records.db join feedback.db → MAE vs baseline → 超 1.3 倍红字告警 + drift_log.csv 留档
- **训练责任人**：用户自己（**2026-08-31 拍板**）

### 2026-08-28 · Phase 22 B/C/D 生产闭环

- **B 特征重要性月报脚本**（用户拍板：月报 + 自己看为主）：tools/print_feature_importance.py（217 行）+ humanizer + 月度快照对比 + Top10 涨/跌标。首次跑：正文长度 35.19% / 标题长度 22.92% / 高效词命中 14.59%
- **C 漂移自动回退**（用户拍板：自动切回 L0）：core/active_mode.py 三态 + monitor_l1_drift.py apply_auto_rollback；workflow：drift → 写文件 → 01 启动读 → 黄 banner 提示
- **D 批量预测自动落档 records.db**（用户口径：批量跑的预测一定会投出去）：batch_evaluation_service.save_predictions_to_records + 03 checkbox 默认关按需开启
- 总用例 697 → 794 PASS

### 2026-08-28 · Phase 22 A.1 产品权益维度扩展

- **拆字段**：TaskInput.product_benefit → product_category + benefit_type（启用，**不参与 CTR baseline**——Phase 9 拍板 baseline 数据稀疏 ROI 低；只影响 ① AI prompt 注入 ② 产品词典 jieba 词条扩展）
- **数据源**：config/product_benefit.yaml（10 产品 + 8 权益 + custom_label）+ core/product_benefit.py 加载模块
- **dataclass 字段顺序铁律**：audience/channel/stage/tone → expected_action/.../extra_requirements → product_category/benefit_type（新启）→ objective（灰态）→ text_has_coupon
- **A.2 投放目标暂搁**：用户口径"投放目标可以写待开发，跟 L2 和 UI 坐一桌"
- 总用例 794 → 823 PASS

### 2026-08-28 · Phase 23+24 安全加固 + 全量 sweep

- **Phase 23 Critical-1/2 安全加固**：API key 泄漏（_sanitize_error + _classify_call_error）+ XSS（html.escape）+ page_setup 模块抽取 + monitor_l1_drift 修整
- **Phase 24 全量 sweep**：§61 24 用例覆盖 31 模块 import / SQLite tmp dir / rule_engine 4 边界 / ctr 5 modes 全过 / TaskInput 4 必填 / 空 DB 优雅降级。**首次确认 L1 模型 live**
- 总用例 823 → 854 PASS

### 2026-08-31 · Phase 25 代码清理 + Handoff 压缩

- **L1 runbook**：docs/l1-training-runbook.md 落地（5 步流程：训练 → 切 L1 → 监控 → 自动回退 → 月报）
- **频率改月度**：docs/ctr-feedback-schedule.md 从"每周一上午"改为"每月 1 号上午手动"（用户拍板）+ §3.5 加 L1 漂移监控步骤
- **死代码清理**：tools/push_*_via_api.py ×9 → tools/_archive/ + ui/plotly_helpers.py axis_rate() 删 + 2 unused import 删
- **L1 CSS 补齐**：ui/styles.py 加 .l1-pill/.l1-label/.l1-value/.l1-meta 4 个类（之前 01 引用但未声明）
- **black 格式化**：ui/styles.py / pages/01/02 三文件
- **Handoff 压缩**：4 文件全整理（Phase 1-10 早期决策压 1-2 行 + why；Phase 11+ 保留）
- verify 854 PASS（无回归）

---

## §5.5 CTR 准确率学习 Roadmap（2026-08-26 · 重要背景）

**完整原文**：`Downloads\CTR准确率学习-Roadmap附录_2026-08-26.md`。**此处给执行摘要**。

**一句话**：把 CTR 从"查找表统计校准"升级到"会自我度量、会重训的回归模型"，让"**预测误差 vs 真实 CTR 曲线**"往下走。

### Phase 16 维度扩展决策（2026-08-27 · 用户拍板）

口径：「**预算owner 不加，工作日类型从 sent_date 推算就行，标题正文是否带券加一下，其他不用**」。

- ✅ 加 `text_has_coupon`（Phase 15 已建维度，Phase 16 接入回流反馈聚合）
- ✅ 加 `工作日类型`（从 `sent_date` 推 `工作日`/`非工作日`，复用 `core/data_window.classify_date_type`）
- ❌ 不加 `预算Owner`（用户拍板"不加"）
- ❌ 不加 `title_len_range`（用户拍板"其他不用"）
- 落地：`tools/calibrate_baseline.py` 覆盖 4 维度（渠道 / 渠道×用券 / 渠道×文案含券词 / 渠道×工作日类型）；`baseline_lookup` 已支持；`feedback_records` 表加 `text_has_coupon TEXT` 列 + ALTER 兼容老库

### 三台阶

| 台阶 | 做法 | 触发 | 状态 |
|---|---|---|---|
| **L0（现状）** | baseline 查找表 + `calibrate_baseline.py` EMA | ✅ 已建（Phase 5 P2） | ✅ 投产 |
| **L1** | LightGBM 回归替查找表（15 维） | ✅ Phase 18-20 落地 | ✅ 投产（runbook 详 5 步流程） |
| **L2** | 增量重训 + 上线前回测门禁 + 误差监控 | L1 稳定后 | ⏳ 待启动 |

### 当前断点

```
①生成 → ②预测 → ③投放 → ④回收真实 CTR
                                ↓
                          ⑤ 重训模型（runbook 详）
```

①②③④ Phase 5 管道已搭（P0 signature + P1 feedback + P2 calibrate），断点在 ⑤（用户手动跑 runbook 流程）。

### 选型铁律 · 为什么是 GBDT 不是深度学习

- 输入是**结构化表格特征** + **中样本** → LightGBM 几乎必然赢神经网络
- GBDT 出**特征重要性**（可解释是刚需）—— 业务要能问"为什么这个 Plan CTR 高"
- 深度 CTR 模型（DeepFM/DIN）要**亿级样本**才回本，本项目喂不饱，别上

### 务实节奏（防过拟合）

- **短期（< 几百条）**：维持 L0 EMA；先把误差曲线搭起来
- **中期（~ 千条）**：切 L1（Phase 18-20 已落地，runbook 详 5 步流程）
- **长期**：L2 增量重训 + 回测门禁（待 L1 稳定）

### 与决策文档联动

CTR 学习 ≠ 复杂模型，但**首先得有"准确率"可量化的指标**——这要先定**口径**（决策文档 #5）。口径不定，**算不出误差** → L1 全免谈。

---

### 2026-09-01 · Phase 28 必填口径改 3 项 + 「通用（不指定）」

- **表单必填从 5 项砍到 3 项**（投放渠道 / 目标人群 / 内容语气），其余 9 项全部可选
- **可选字段第一项加「通用（不指定）」默认选中**，后端 prompt 拼装 + Demo 占位候选遇此值整行跳过（让 AI 自由发挥）
- **改 6 文件**：core/schemas.py（5 enum + REQUIRED_FIELDS 改 3 项）+ tests/verify.py（必填测试同步）+ web/templates/pages/01_内容工坊.html（重排字段顺序 + selectbox 选项）+ prompts/copy_generation.py（v1.1→v1.2 通用跳过）+ services/generation_service.py（_demo_candidates 通用跳过）+ PRD.md §6.2 字段表
- **why**：硬必填的判定标准 =「下游 pipeline 不填跑不通」；阶段/场景/投放目标等是 LLM 文案素材，可走默认让 AI 自由发挥

### 2026-09-01 · Phase 29 候选展示翻牌（推翻 #6）

- **#6 反哺影响生成排序** Phase 7.2 拍板作废 —— 候选展示**不再**按 CTR 重排，固定 A→B→C 顺序
- **默认选中** 改硬编码 "A"，不再是 CTR 最高那条
- **CTR 反哺**：仍展示在右侧"参考结果"（CTR 数字 + 相对基准百分点），影响「可信程度」标注，但不参与卡片排序
- **why**：用户复盘"竖着文案很奇怪"时同步反馈——ABC 顺序乱 + 默认选 B/C 让"选 A"操作不直觉；CTR 反哺作为参考信息已足够，不该把"参考"上升为"推荐排序"
- **改 3 文件**：web/app.py（删 `rank_candidates_by_ctr` 调用 + `selected_id` 写死 "A"）+ web/static/css/style.css（candidate-card 加 min-height:210px 让 3 卡等高；cand-body line-clamp 5 行 + cand-title line-clamp 2 行避免长 body 折成多行挤压竖排感）+ Handoff-decisions.md（本段）
- **保留**：services/generation_service.rank_candidates_by_ctr 函数本身不删（tests/verify.py §42 测试照常 PASS），只是 web 层不再调用

### 2026-09-01 · Phase 31A L1 混合校准（不重训接 baseline 6 维）

- **痛点**：L1 LightGBM 训练 R²=0.08（区分能力差），但 absolute MAE=0.34% 尚可；baseline_lookup 6 维回退查表有数据基础但稀疏维度兜底到渠道整体；两边互补
- **方案 A 拍板**（用户选择"不重训 + 混合校准"）：L1 推理后叠加 baseline_lookup × tm
  - `final = 0.5 × l1_pred + 0.5 × (baseline × tm)`（baseline 有值时，50/50 平权）
  - `final = l1_pred × tm`（baseline 缺失时，仅 L1 相对量级 + 时段修正）
- **为什么不选 B/C**：
  - B 重训加 text_has_coupon + char_range + hour + baseline 6 维数值特征：2-3 天工作量，且 text_has_coupon 短信 62 Plan / 企微 189 Plan 数据稀疏，重训 R² 改善不确定
  - C 主路径换 baseline_only：L1 模型白训、Handoff §6.3 L2 重训任务推后
- **改 2 文件**：adapters/ctr_predictor_adapter/__init__.py（`_l1_model_pred` 加 L1_BLEND_ALPHA=0.5 + 双分支混合公式 + suggestion 文案带 50/50 字样 + source 改 `ctr_predictor_adapter/l1_blended`）+ tests/verify.py（§57 l1_model source 断言从 `l1_lightgbm` 改成 `l1` 兼容 l1_blended / l1_lightgbm）
- **不动**：L1 booster 模型、meta、baseline_lookup、train_lgbm.py；UI 顶部 mode 选项仍 l1_model（路径不变）

### 2026-09-01 · Phase 32 算法模型显示名纠正

- **痛点**：Phase 27 把 CTR 模式 UI 标签改成产品话术时，`XGBoost` 是误称（底层实际是 LightGBM），会让运营同事去查 XGBoost 文档发现对不上；`渠道基线` 只覆盖 6 维回退第一维，命名不准
- **改 3 行**（web/templates/pages/01_内容工坊.html 顶部 selectbox）：
  - `演示规则` 保留（无歧义）
  - `渠道基线` → `历史基准`（覆盖 6 维回退全维度）
  - `XGBoost` → `LightGBM`（底层真实模型名）
- **不动**：`value` 属性（demo / baseline_only / l1_model 后端 mode 值不变）；`selected` 判断不变；CSS class 不变；后端逻辑完全无影响

### 2026-09-01 · Phase 38 A1-mid 22 处 inline style 收敛 + design.md §0.1 DNA + §12 避坑

- **问题发现**：Handoff §6.0 写「847 PASS / 0 FAIL」但实际跑是「842 PASS / 5 FAIL」—— 5 FAIL 全是 verify.py 同步漂移（Phase 28 / Phase 30 改 schema 时 verify.py 没同步 5 处断言）。**这是「Handoff 文档 vs 代码数字」系统性脱节**，详见 design.md §12.1。
- **范围拍板**：用户走 A1-mid 范围（修 22 inline + design.md 增量 + 5 FAIL 同步），不动 A1-min / A1-full。
- **22 处 inline 收敛**：8 个新 CSS 类（form-grid-tri/quad、metric-row-tri/quad/bi/spaced、card-desc-spaced/spaced-sm、subsection-tight、stat-line-muted、link-download）+ 4 条自动间距规则（.kpi-tile + .kpi-tile / .candidate-card + .candidate-card / .panel-card .warning-banner / .panel-card .batch-wrap）。
- **design.md 增量**：§0.1 一句话定义 + 参考 Layer 0（OneDrive DESIGN.md 通用哲学）/ §5 历史收敛记录 / §6.7-§6.9 新模式 / §10 AI Agent 5 步流程 / §11 质量检查清单 / §12 避坑教训 4 条 / 附录 A 48→60 类 / 附录 B 变更日志。
- **配套**：04_历史洞察.html `<title>` 去前缀 `04 历史洞察` → `历史洞察`（Phase 27 URL 语义化尾巴）。
- **唯一残留 inline style**：01 内容工坊主按钮业务特化（allowlist 注释，§9 lint 跳过）。
- **why**：22 处里有 4 种重复模式（form-grid 列数变体 / metric-row 列数变体 / card-desc 间距 / form 后短说明），说明 design.md §2.6「表单」和 §2.8「KPI」之前没把变体列全。本次抽 8 个类补全，§12.2 避坑记录「≥3 处同模式必抽类」。
- **verify.py 同步 5 处**：① Phase 28 必填 4→3 / ② Phase 30 options_with_custom +1→+2 / ③ PLAN_TYPES 3→4 / ④ llm_status 默认测试用 tmpdir 隔离 yaml / ⑥ sweep TaskInput stage 选填跳过。
- **3 commit 推送**：fd94aea（fix: A1-mid）/ 816eb85（docs: §12 避坑）/ f7835ef（chore: 归档 push 脚本）。**远端 HEAD**：6e0be2cf7db6。
- **顺手修脚本 bug**：push 脚本 archive 嵌套路径需 `.parent.parent.parent`（原 `.parent.parent` 只到 tools/，导致走「删除文件」分支 422 BadObjectState）。下次 archive push 脚本直接用这个修正。
- **验证**：848 PASS / 0 FAIL（含 1 新增 options_with_custom 首位 = 通用）+ inline style 1 处 allowlist + py_compile web/app.py 全过。

### 2026-09-02 · Phase 40-43 字典维护鉴权 + 3 个连环 BUG 修复

- **Phase 40 字典鉴权 + 左侧栏隐藏**：
  - 用户拍板"左侧栏不显示字典维护入口 + 简单密码鉴权（密码 `ori1026`，无 SSO）"
  - `web/app.py` `NAV_PAGES` 加 `hidden_in_nav: True` 标记 settings 项；`base.html` nav 循环跳过 `hidden_in_nav` 项
  - 新增 `SETTINGS_PASSWORD` / `SETTINGS_COOKIE_NAME` 常量 + HMAC-SHA256 签名 cookie（`httponly + samesite=lax + path=/`）+ `_make_settings_cookie` / `_verify_settings_cookie` / `_settings_auth_or_redirect` helper
  - 新增 3 个路由：`GET /settings/login` / `POST /settings/login` / `GET /settings/logout`
  - 现有 `/settings` + `/api/settings/save` + `/api/settings/download` 全部加鉴权装饰
  - `home.html` 字典管理区底部「停用词」行（× icon）
  - `web/templates/pages/06_settings_login.html` 新建（简洁居中卡片）
  - `static/css/style.css` 加 `.settings-head` + `.login-wrap`
- **Phase 40 BUG**：cookie `path=/settings` 严格匹配 → `/api/settings/*` 不在 cookie 路径下 → 浏览器不发 cookie → 全 401。**修**：改 `path=/`。
- **Phase 41 textarea 双重 escape BUG + 加 stopwords 字典**：
  - **问题**：Jinja autoescape + `| e` 双重 escape → `&#34;` 等 entity 字符串写进 textarea → 浏览器 textarea **不解析 HTML entity**（与 input 不同）→ 数据乱码
  - **修**：textarea 内容改 `<script type="application/json" id="dict-init-X">{{ d.content | tojson }}</script>` + JS 读 `.textContent` 后 `JSON.parse` 填入 textarea
  - **加 stopwords 字典**：`DICTIONARIES` 加 stopwords 项（5+1=6 个字典）；`_write_dict_file` 加 stopwords reload 分支
- **Phase 42 textarea `\n` attribute 截断 BUG**：
  - **问题**：HTML5 spec attribute value 遇 LF 截断。tojson 输出 `"word1\nword2"`，HTML parser 在 `\n` 处截断 attribute → 数据丢失
  - **修**：tojson 输出挪到 `<script type="application/json">` tag（script 标签内容可以是任意字符包括 \n，HTML parser 不截断）
  - **JS 路径**：document.querySelectorAll('textarea[data-init-id]').forEach → JSON.parse(scriptEl.textContent) → ta.value
- **Phase 43 双 CR BUG + .gitattributes 防御**：
  - **问题**：浏览器 textarea 写 LF + Windows git autocrlf 把 LF 转 CRLF 但因为历史 CRLF 残留 → commit 时叠加变成 `\r\r\n`（双 CR，UTF-8 不报错但显示有 ^M^M）
  - **修**：
    1. Python 脚本清空 `custom_dict.txt` 双 CR + 空行（135 行 → 68 行 67 词，纯 LF）
    2. 新建 `.gitattributes` `data/*.txt text eol=crlf`（防止 git autocrlf 叠加造成 `\r\r\n`）
    3. `_write_dict_file` 写 text 类字典统一 CRLF：`content.encode("utf-8").replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")`（textarea 写 LF + Windows autocrlf 双 CR 防御）
    4. yaml/json 保留原样（保留缩进）
- **不动**：业务层 0 行改动；HMAC-SHA256 secret 从 `SECRET_KEY` env 拿（Phase 25 已有约定）；Phase 26 5 页面 + 13 API 路径全保留
- **为什么 4 个 phase 串成一周**：用户先报"左侧栏藏 + 加密码"（Phase 40），然后报"产品字典缺 stopwords"（Phase 41），然后报"保存后内容换行混乱"（Phase 42 → Phase 43）。3 个连环 BUG 全部从「Jinja autoescape → HTML attribute → CRLF line ending」一层一层挖出来。每个修一个再触发下一个。
- **验证**：`python tests/verify.py` 仍 **848 PASS / 0 FAIL**（无回归）；smoke 7 case 全过（settings 鉴权链路 + 字典读写 + cookie path 修复）
- **Commit**：`d6417c9`（本地 + 远端 `32508fb3bd62`）—— `.gitattributes` + `web/app.py` + `data/custom_dict.txt`

### 2026-09-02 · Phase 44 _write_dict_file 4 重防御（双 CR + 空行 + trailing space）

- **问题复盘**：用户再次报"保存后中间插入一行空格"——Phase 43 的 `replace(\r\n → \n).replace(\n → \r\n)` 没防住**回旋效应**场景：当 input 含历史 `\r\r\n` 双 CR 时，**第一次 replace 只吃掉 CRLF（第二个 + 第三个字节），剩下孤 `\r`**，**第二次 replace 之前，孤 `\r` 还在**，第二次 replace 把 `\n` 转 `\r\n`，但孤 `\r` 前面没东西——实际结果：第一次 replace 输出 `b"的\r了\r和\r"`（保留所有第一个 `\r`），第二次 replace 不动（没匹配）→ 输出还是 `b"的\r了\r和\r"`。

  **但是**：用户保存的 input 是 read_text 之后的 LF only（universal newlines 模式），**理论上不会有 `\r\r\n` input**。那 `\r\r\n` 怎么来的？**唯一可能**：之前 gitattributes + autocrlf 把已 CRLF 的 working tree 重新 normalize 一次（叠加），或者保存链路中间有别的路径。

- **新算法（彻底防御）**：
  ```python
  raw = content.encode("utf-8").replace(b"\r\n", b"\n").replace(b"\r", b"\n")
  lines = [ln.rstrip() for ln in raw.split(b"\n") if ln.strip()]
  tmp.write_bytes(b"\r\n".join(lines) + b"\r\n")
  ```
  - ① **CRLF / 孤 CR 全部归一 LF**：破回旋效应（先 replace `\r\n` → `\n`，再 replace `\r` → `\n`，无论 input 怎么混合都归一）
  - ② **过滤空行**：HEAD stopwords.txt 原含 1 空行（`\r\n\r\n`），用户保存后被规范化过滤掉
  - ③ **每行 rstrip 去行尾空格**：保留前导缩进（jieba load_userdict 用空格分隔词频）
  - ④ **输出 CRLF + trailing CRLF**：跟 gitattributes `eol=crlf` 一致
  - **保留 `#` 注释行**：jieba load_userdict 容忍 `# 开头`（不参与分词）

- **验证**：
  - **16/16 单元测试**：`tmp_normalize_test.py` 覆盖 LF / CRLF / 双 CR / 孤 CR / 混合 / 空行 / whitespace-only / 前后空格 / 无 trailing newline / 中文
  - **smoke e2e**：注入 `\r\r\n`（78 处）→ 输出 77 CRLF + 0 双 CR ✓；注入空行（68 处 × 2 LF）→ 输出 68 行 + 0 空行 ✓
  - **回归**：`python tests/verify.py` **848 PASS / 0 FAIL**（无回归）

- **为什么换"表格"方案没用**：用户试探"实在不行要不要换表格"——表格方案（每行一个 input + JS add/row）虽然每行自动 trim 不易污染，但要重写 JS 加 add/row，对 jieba hot reload 路径不友好（要 join `\n`）。**4 重防御已经能防住所有 line ending 边界**，表格方案作为备选留待后续。

- **顺手修 push 脚本 bug**：archive 嵌套的 `push_phase43_via_api.py` 用 `.parent.parent` 计算 ROOT（只到 tools/），但实际脚本在 `tools/_archive/` 里，应该是 `.parent.parent.parent`（多一层）。**Phase 38 A1-mid 教训 §13 复现**，又踩了一次。修后推送成功。

- **Commit**：`3ba20c5`（本地 + 远端 `956ec3b64cd8`）—— `web/app.py` 1 文件 +10 -4 行。

### 2026-09-02 · Phase 45 字典本地备份（CLI + 自动触发双方案）

- **用户需求**：担心字典维护手残误删，本地每天有备份。

- **第 1 版（CLI 脚本）**：
  - `tools/backup_dicts.py` 主备份脚本（CLI + 内化 API）
  - `tools/backup_dicts.bat` 双击便捷调用（CRLF UTF-8，按 §8 教训强制 CRLF）
  - `.gitignore` 加 `data/.backups/`（不污染 git）
  - 备份 7 个字典文件：custom_dict/stopwords/ctr_baseline/channel_rules/dimension_weights/coupon_keywords/brand_rules
  - 输出 `data/.backups/dicts_YYYY-MM-DD_HHMMSS.tar.gz`
  - 保留 14 天（自动清理）
  - 提供可选 schtasks 命令示例（用户可加自动每日定时）
  - **Commit**：`8d09f71`（本地 + 远端 `6a7ad524869c`）

- **第 2 版（用户反馈：应该是每次保存时自动备份）**：
  - 用户原话："应该是我明白次保存，比如上一次记录是昨天，我今天点了，昨天的就备份了，是不是应该这样"
  - **理解**：用户要的不是定时 cron，而是**用户每次点 settings 页面「保存」按钮时自动备份**——"改动即留档"。
  - **去重**：每天首次保存才创建备份（同一天多次保存不产生多个 tar.gz）
  - **改动**：
    - `tools/backup_dicts.py` 拆出 `has_backup_today()` + `create_backup_internal(days=14)` 内部 API（web handler 可调用）
    - `web/app.py` `settings_save` 在 `_write_dict_file` 成功后调用 `create_backup_internal`
    - flash_msg 拼上备份信息（用户每次保存看到）
    - 备份失败 try/except 兜底，**不影响保存流程**
  - **flash 文案**：
    - 首次保存：「产品词典 保存成功 · 已自动备份 7 个字典文件 (19,309 字节)」
    - 同天重复：「产品词典 保存成功 · 今天已备份过（dicts_2026-09-02_153217.tar.gz），跳过」
  - **Commit**：`4c032a6`（本地 + 远端 `51ed42480e56`）—— `tools/backup_dicts.py` 内化 API + `web/app.py` settings_save hook

- **设计细节**：
  - **tar.gz 压缩比**约 3x（19KB 原始 → 7KB 压缩）
  - **去重逻辑**：`has_backup_today()` 检查 `dicts_YYYY-MM-DD_*.tar.gz` 文件名（glob 前缀匹配）
  - **清理逻辑**：每次备份后跑 `cleanup_old(days=14)`，删除超过 N 天的
  - **失败容错**：备份异常 try/except 兜底，不会因备份失败阻塞保存
  - **双重保险**：本地 tar.gz + 远端 git 历史，恢复任意层

- **验证**：
  - e2e smoke：首次保存 → 1 个备份 / 同天重复 → 仍 1 个备份 + 跳过消息
  - `python tests/verify.py` **848 PASS / 0 FAIL**（无回归）

- **不动**：
  - 第 1 版的 CLI `.bat` 双击方案保留作为手动备份入口（用户偶尔想强制备份完整周报时用）
  - schtasks 自动定时方案**作废**（用户选了保存时自动触发，不需要定时）

---

## Phase 46 · 2026-09-02 · 历史洞察 4 BUG 修复 + 3 Tab 查询增强

**用户原话**："再检查一下吧，我还是发现很多BUG的，比如 http://localhost:8530/insights?tab=wf 的选词对比... 然后不知道这个是什么点击后会报错：http://localhost:8530/insights?tab=daily 点击后 Internal Server Error"

**用户原话（追加反馈）**：
- "还有 BUG，我在高低表现词，输入了一个词后，点击搜索，跳回了高效 plan 排行"
- "单词对比我觉得应该放到查询下面... 但是这样页面会跳动一下对吧，有更好的解决方案吗？"
- "我发现 emoji、高效 plan 排名，这两个没有输入的按钮，不能查询指定的 plan 和 emoji"

**4 个 BUG + 3 Tab 查询增强**：

### BUG 1 · daily 500（pandas round() 不接受 pd.NA）

**根因**：`services/analytics/daily_trend.py:91` 周环比计算时 `_ctr_shift` 分母为 0 → `pd.NA` → 整个 ratio Series 含 NA → `.round(2)` 抛 `TypeError: type NAType doesn't define __round__`。

**修法**：`ratio_pct = ratio_pct.astype("Float64")`（nullable type）后再 `.round(2)`（pandas 2.0+ 支持 round on Float64 with NA preserved）。

**教训**：pandas 2.0+ nullable types (`Float64`/`Int64`) 跟默认 numpy types 行为不同；任何 `.round()` / 数学运算前先想清楚 NA 处理。

### BUG 2 · wf 选词对比 select → input

**用户原话**："应该是输入关键词查询指定词，而不是选词。因为有很多词"

**修法**：`04_word_freq.html` `<select name="wf_compare_sel">` → `<input type="text" name="wf_compare_sel" placeholder="任意词，含/不含 plan CTR 对比" maxlength="32">`；CSS 加 `.form-row-span2{grid-column:span 2}` 让输入框跨 2 列；base.html 缓存 `?v=20260902wf`。

### BUG 3 · wf 提交后 tab 跳回 rank（所有 6 个 tab 同病）

**根因**：`web/app.py:1001` `active_tab = request.query_params.get("tab", "rank")` —— 表单不传 tab → 默认 rank。wf/ef/sim/owner/daily 5 个表单全部缺这个 hidden field。

**修法**：6 个 tab form 全部加 `<input type="hidden" name="tab" value="X" />`：
- `04_rank.html` → tab=rank
- `04_word_freq.html` → tab=wf
- `04_table.html` → tab=ef
- `04_similar.html` → tab=sim
- `04_owner.html` → tab=owner
- `04_daily_trend.html` → tab=daily（这个其实原本就有，但保险起见也加了）

**教训**：多个 form 共享同一查询 URL + 后端 default tab → **每个 form 都要主动传 tab**，不能依赖 default。

### BUG 4 · 单词对比位置 + 页面跳动

**用户原话**："单词对比我觉得应该放到查询下面... 但是这样页面会跳动一下对吧"

**分析**：之前表单 → 高效词 → 低效词 → 单词对比；输入词提交后单词对比在屏幕下方，需要下滑。Phase 36 的 scroll restore 虽然在工作，但本质问题是"对比不在视口内"。

**修法**（用户原话"有更好的解决方案吗" → 答"有"）：把 单词对比 移到 表单 紧下方 → 高效词 → 低效词。input/output 一对贴一起，提交后对比区块就在视口里，**自然不依赖 scroll 恢复**，base.html 的 Phase 36 滚动机制保留继续生效。

### 增强 1 · rank Tab 加 "输入 Plan ID 查详情"

**用户原话**："高效 plan 排名没有输入的按钮，不能查询指定的 plan"

**改动**：
- `04_rank.html` 表单加 `<input type="text" name="rank_plan_sel" placeholder="单个 plan 详细元数据 + CTR" maxlength="64">`
- `web/app.py` 新增 `_plan_detail(df, plan_id) -> Optional[dict]` helper（字段对齐 `rank_plans` 一行 + 加 title/body 样本）
- `04_rank.html` 加 `{% if plan_detail %}` 区块：触达 / 点击 / CTR / Plan名称 / 渠道 / Owner / 覆盖高效词数 + n_records / n_days / 字数均值 + 样本标题正文

### 增强 2 · ef Tab 加 "输入 emoji 查对比"

**用户原话**："emoji 没有输入的按钮"

**改动**：
- `04_table.html` 表单加 `<input type="text" name="ef_compare_sel" placeholder="任意 emoji..." maxlength="16">`
- `web/app.py` `ef` 分支调 `compare_token(df, sel, col="_emojis")`（`text_analyzer.py` 已有 `_emojis` 列，复用 wf 路径）
- 加 `{% if ef_compare %}` 区块：含 emoji plan 触达 / 不含 plan 触达 / delta_pp / 含 CTR / 不含 CTR / n_plans_with/without

### 踩坑 · Jinja2 `%` 关键字 + `}}%` 解析崩

**坑**：第一次写 `{{ "%.2f"|format(plan_detail.加权CTR%) }}%` —— Jinja2 报 `unexpected ')'`。其他 4 处中文 key（如 `summary['整体CTR%']`）用下标写法都 OK，只有 `.加权CTR%` 这种**点语法 + `%` 关键字结尾**会触发解析器混乱（猜测 Jinja2 lexer 在 `加权CTR` 后看到 `%` + `)` + `}}` + `%` 一连串 token 切分歧义）。

**修法**：全部用 `plan_detail['加权CTR%']` 下标写法。

**教训**（Handoff-lessons.md §19）：Jinja2 模板里 dict key 含 `%` 等特殊字符 → **永远用 `dict['key%']` 下标写法**，不要 `dict.key%` 属性语法。

### 按钮/handler 全量 smoke

17 GET + 12 POST 路由全部 smoke 过：所有 GET 返回 200/303（303 是 /settings auth redirect），所有 POST 返回 303/422/200（无 500）。所有按钮/handler wired 正确，**本轮没有其他未发现的 handler 不一致 BUG**。

### 验证

- `tests/verify.py` 848 PASS / 0 FAIL
- curl smoke：5 个 tab (daily/wf/rank/ef/owner) + 5 个表单提交场景 全 200
- rank_plan_sel=P202410110023 → "Plan 详情 · P202410110023" 区块渲染
- ef_compare_sel=🎉 → "emoji 对比 · 🎉" 区块渲染
- wf_compare_sel=test → "单词对比 · test" 区块渲染

---

## 已压缩删节（细节查 git log）

- `setup_and_run.bat` 闪退 5 次迭代详细历史（v1-v5 各版）
- 早期 verify.py 用例数 82→152 各 phase 增量明细
- 已知小 bug 修复记录（CTR Adapter bl=None、Candidate.id=A/B/C、CSV bytes literal 等）—— 教训已留 `Handoff-lessons.md`
- 推送脚本演进（force-with-lease / Contents API / GitHub secret scanning）—— 教训已留 `Handoff-lessons.md`
