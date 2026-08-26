# CTR 预测反哺闭环 — 思考笔记

> 日期：2026-08-26
> 项目：`mcd-ai-content-platform`
> 触发：用户提出"数据跑出来后，如何反哺之前的 CTR 预测"
> 状态：思考稿，待业务/技术评审后落地

---

## 0. 一句话

把"AI 生成 → 投放 → 回流数据"串成闭环，让 baseline 和维度权重不再是一次性校准、而是**周级别自更新**。

## 1. 三层结构

```
┌──────────────────────────────────────────────────────────┐
│ L1. 闭环链路：record_id + 指纹作为 join 锚点              │
│ L2. baseline 校准：每周自动重算（指数滑动，避免抖动）     │
│ L3. 维度权重：从"查表"升级到"轻量模型"，CTR 真预测       │
└──────────────────────────────────────────────────────────┘
```

## 2. 闭环链路设计

### 2.1 record 指纹（关键前提）

**当前状态**：`records.db` 已存 task 全字段 + candidates + selected_id，但**缺统一指纹**，回流数据 join 成本高。

**修复**：
- 在 `GenerationRecord.to_row()` 追加 `task_signature` 字段（人群-阶段-场景-渠道-字数-必带词指纹）
- 同步在 `services/generation_service.build_record` 计算时填入
- 对应 schema：`core/schemas.GenerationRecord.signature: str`

**理由**：回流 Excel/CSV 大概率不含完整文案，只有标题 + 触达/点击数据。指纹让我们不用解析文案就能 join 维度组合。

### 2.2 feedback 数据流

```
回流 Excel (业务方)
   ↓ upload_feedback_page (Phase 4.5 新建)
data/feedback.db (新表 feedback_records)
   ↓ scheduled / threshold 触发
tools/calibrate_baseline.py v3.1
   ↓
data/ctr_baseline_v3.1.json (版本号 + 1)
   ↓
adapters/ctr_predictor_adapter/baseline_lookup.py
   （按 baseline_version 字段读取对应版本）
```

### 2.3 反馈表最小 schema

```sql
CREATE TABLE feedback_records (
    id INTEGER PRIMARY KEY,
    task_signature TEXT NOT NULL,    -- join 锚点
    channel TEXT NOT NULL,           -- 冗余，便于查询
    coupon TEXT,                     -- 冗余
    plan_type TEXT,                  -- 冗余
    sent_date TEXT,                  -- 发送日期 (YYYY-MM-DD)
    reach_success INTEGER,           -- 触达成功
    click_count INTEGER,             -- 点击人次
    order_count INTEGER DEFAULT 0,   -- 下单人次（可选）
    source TEXT,                     -- 回流来源文件名
    imported_at TEXT DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX idx_feedback_sig ON feedback_records(task_signature);
```

## 3. baseline 校准机制

### 3.1 口径（CLAUDE.md §9 已定）

```
actual_ctr = sum(点击) / sum(触达成功)
baseline[维度组合] = Σ实际 / Σ期望触达
```

### 3.2 冷启动 vs 热更新阈值

| 维度组合样本量 (n_plans) | 策略 | 备注 |
|---|---|---|
| < 5 | 用历史 JSON 不动 | 样本不足，不校准 |
| 5 ~ 20 | 部分校准（指数滑动，α=0.3） | 让新数据有声音但不让它翻盘 |
| ≥ 20 | 全量校准 | 样本够稳 |

### 3.3 指数滑动公式

```
new_baseline = α * computed_baseline + (1 - α) * old_baseline
α = 0.3（n_plans < 20 时）
α = 1.0（n_plans ≥ 20 时）
```

**为什么不用全量覆盖**：单次活动数据可能极端（爆款或翻车），一次性覆盖会让 baseline 大幅抖动，影响后续预测稳定性。

### 3.4 工具化

现有 `tools/calibrate_baseline.py` 升级：
- 接 `data/feedback.db`（新增）
- 输出 `data/ctr_baseline_v3.x.json`（版本号 + 1，写入 meta.version）
- 触发方式：**双触发** — 周一凌晨定时 + 当新数据 ≥ 100 条时手动/自动跑

### 3.5 离线评估（不留没测的校准）

每次校准后：
- 最近 10% 数据做留出验证集
- 输出一份 `eval_reports/calibration_v3.x.md`：
  - MAE：baseline 预测值 vs 实际值的平均绝对误差
  - 方向准确率：baseline 预测方向（高/中/低）vs 实际方向
  - **不写预测准确率**（PRD §3.2 红线）

## 4. 维度权重动态调整

这是 CTR 从"查表" → "预测"的关键升级。

### 4.1 当前状态

`adapters/ctr_predictor_adapter/baseline_lookup.py` 是固定 7 维度查表（channel / coupon / plan_type / day_type / title_length_bucket / audience / scene），没权重概念。

### 4.2 升级路径

```
历史 plan 数据 → 特征工程 → 轻量模型 (logistic / GBDT)
   ↓
特征重要度排序
   ↓
写回 config/dimension_weights.yaml (新)
   ↓
baseline_lookup._apply_dimension_weights() 应用
   ↓
ctr_prediction_service.predict_for_candidates 加 weights_version 参数
```

### 4.3 实现位置

| 模块 | 改动 |
|---|---|
| `config/dimension_weights.yaml` (新) | 7 维度的权重（默认全 1.0） |
| `adapters/ctr_predictor_adapter/baseline_lookup.py` | 加 `_apply_dimension_weights()` |
| `tools/train_dimension_weights.py` (新) | 跑模型 → 输出 yaml |
| `services/ctr_prediction_service.py` | 接受 weights_version 注入 |
| `pages/01_content_studio.py` | 在 CTR 卡片显示 "权重版本 v1.x" |

### 4.4 模型选型

不引入 sklearn 依赖（保持轻量）：
- 优先：**逻辑回归**（手写 SGD，几十行）
- 备选：调 `python -m sklearn.linear_model.LogisticRegression`（如已装）

**不引入** 复杂模型（GBDT / NN），理由：样本量在百 ~ 千级别，复杂模型会过拟合。

## 5. 业务侧闭环（4 个阶段）

| 阶段 | 投入 | 产出 | 可见价值 |
|---|---|---|---|
| **P0** record 指纹 + record_id 落库 | 0.5 天 | 回流数据有 join 锚点 | 基础 |
| **P1** feedback.db + 上传页（Phase 4.5） | 1 天 | 数据进得来 | 入口 |
| **P2** calibrate_baseline 自动化 | 1 天 | baseline 不再是死的 | baseline 自更新 |
| **P3** 维度权重动态调整 | 3 天 | CTR 真预测 | 准确率提升 |
| **P4** UI 显示反哺状态 | 0.5 天 | 业务方知道用的是哪版 | 透明可信 |

**最小闭环 = P0 + P1 + P2，3 周内跑通。**

## 6. 与现有架构的对应

| 现状 | 反哺改动点 |
|---|---|
| `data/ctr_baseline.json` v3.0 静态 | → `ctr_baseline_v3.x.json` 多版本 + `meta.version` |
| `tools/calibrate_baseline.py` 一次性 | → 接 feedback.db + 定时触发 + 留出验证 |
| `records.db` 只存生成记录 | → 加 `task_signature` 字段 + 新表 `feedback.db` |
| `baseline_lookup.py` 固定查表 | → 加 `_apply_dimension_weights()` 层 |
| `predict_for_candidates` 无版本号 | → 加 `weights_version` / `baseline_version` 参数 |
| 01 创作页 CTR 卡片无来源标签 | → 加 "数据版本 v3.1 / 模型权重 v1.2" 标签 |

## 7. 风险与对策

| 风险 | 对策 |
|---|---|
| 单次活动数据极端，污染 baseline | 指数滑动（α=0.3），不一次性覆盖 |
| 维度权重过拟合 | 简单模型 + 留出验证 + 特征重要度监控 |
| 回流数据 schema 不稳定 | 上传页强制校验 schema，必填列缺失拒收 |
| UI 不知道用的是哪版 | CTR 卡片明示 baseline_version / weights_version |
| 业务方不理解"反哺是什么" | P4 加解释 tooltip：「本次预测基于 v3.x 共 N 条 Plan 数据」 |

## 8. 下一步行动（按用户拍板）

本 session 仅**写思考笔记**，不动代码。Phase 4 三个页面（02/03/04）继续做。

下一 session 候选任务：
- **P0**：在 `GenerationRecord` 加 `signature` 字段 + verify.py 用例
- **P1**：新建 `pages/05_feedback_upload.py` + `data/feedback.db` schema
- **P2**：升级 `tools/calibrate_baseline.py` 接 feedback.db
- **P3**：新建 `config/dimension_weights.yaml` + `train_dimension_weights.py`

---

## 附录 A：相关文件路径

| 路径 | 用途 |
|---|---|
| `data/ctr_baseline.json` | 当前 baseline v3.0 |
| `tools/calibrate_baseline.py` | 现有离线校准脚本（待升级） |
| `repositories/sqlite_repository.py` | records.db 操作 |
| `adapters/ctr_predictor_adapter/baseline_lookup.py` | baseline 查找（待加权重层） |
| `core/schemas.py` GenerationRecord | 待加 signature 字段 |
| `services/generation_service.py` build_record | 待填 signature |

## 附录 B：与 Handoff.md / CLAUDE.md 衔接

- Handoff.md §3 复用清单：本笔记是"超出复用清单的新增工作"，不入复用清单、入待办
- CLAUDE.md §4.2 CTR 四态：反哺后需补 baseline_version 维度（5 态？）—— 暂定 baseline_version 是 PredictionResult 的元信息字段，不影响 result_type 四态分类
- CLAUDE.md §4.3 数据契约：baseline 多版本化是契约扩展，需同步更新 baseline_lookup 读取逻辑