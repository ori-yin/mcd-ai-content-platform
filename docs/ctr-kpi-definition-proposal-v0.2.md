# CTR 口径定义 · 已拍板 v0.2（2026-08-26）

> **状态**：v0.1 倾向稿 → **v0.2 业务已拍板**（Q1-Q6 全部回信 + 取数铁律 + 回传机制确认）。
> **v0.1 保留作历史**，见 `docs/ctr-kpi-definition-proposal-v0.1.md`。
> **目标读者**：实现侧（Phase 6 P2+）+ 数据方后续审计。

---

## 1. 一句话

> **plan 加权 CTR = `sum(plan.clicks_dedup) / sum(plan.reach_success)`**
>
> 渠道不跨合 · 全周期不截断 · `min_reach ≥ 1000` 兜底 · **取数按 `bi_dt` T-1 快照**

口径一旦落地，反哺的全套链路（signature 算误差 / calibrate_baseline 校基线 / L1 GBDT 训练标签）都建在**这个定义**之上；任何一处不一致，反哺存的就是错的 → L0 校准和 L1 训练全部建在沙上。

---

## 2. Q1-Q6 拍板结果

| # | 维度 | 拍板 | 业务语义 |
|---|---|---|---|
| Q1 | 分子 | **B · 去重点击人次** | 同一人重复点同一条 plan 只算 1 次；不同 plan 本来就分开统计，不受此去重影响（"一人点两条不同消息"两条都照常各自计数） |
| Q2 | 分母 | **A · 触达成功** | 发送系统报的送达数，与现 `data_loader` 字段一致 |
| Q3 | 时间窗口 | **A · 全周期不截断** | plan 存续期内点击持续累加，CTR 随之滚动更新，不做 T+1 / T+7 截断 |
| Q4 | 跨渠道 | **A · 不聚合** | 渠道保持为 baseline 维度之一；不引入"全渠道均值" |
| Q5 | 异常处理 | **A → 暂回退 B · 等标注机制就位** | 先用 `min_reach ≥ 1000` 兜底过滤小样本；业务标注机制（重复发送/圈错人群）就位后再切 A 剔除已知问题 plan。**注：小样本（如 100 触达）不属于"异常"，已由 min_reach 阈值处理，不在 Q5 范畴** |
| Q6 | 反哺入口 | **暂不接真实数据** | 业务正式确认前不接真实反馈数据；pages/05_feedback 演示口径保留 |

### 2.1 派生口径（v0.2 暂只算 1 个）

| 指标 | 公式 | 状态 |
|---|---|---|
| **点击率**（主） | `sum(plan.clicks_dedup) / sum(plan.reach_success)` | ✅ v0.2 落地 |
| 转化率 | `click→order` 同口径派生 | ⏳ 业务有需求再加 |
| UV-CTR | `unique_clickers / reach_unique_users` | ⏳ 部分来源缺 unique_users 字段，暂不算 |

---

## 3. 取数时间基准 · 铁律（务必写进 v1.0）

回收真实 CTR 时，时间基准按 **`bi_dt` T-1 快照**：

- 当天 12 点前的查询 → 必须避开当天未生成的快照，**用 `INTERVAL 2` 取前天**
- 当天 12 点后 → 可用 T-1（即昨天的快照）
- 不允许出现"真实 CTR"标签本身取错的情况——否则反哺链路里作为 ground truth 的真实值就是脏的

**铁律**：在 SQL / 取数脚本里写"取 T-1 CTR"前，必须先判断当前时间 ≥ 12 点；否则一律用 `INTERVAL 2` 兜底。

---

## 4. 与现有架构的衔接（v0.2 → 实现侧落地清单）

按 Q1-Q5 + §3 铁律拍板后，已动 / 待动文件：

| 文件 | 改什么 | 状态 |
|---|---|---|
| `data/ctr_baseline.json` | `version=v3.1` + `definition` 字段（"click/触达成功, plan加权, 去重人, 全周期不截断"）+ `min_reach` 阈值字段化 + Q1/Q2/Q3/Q4 边界注释 | ✅ Phase 6 P2 落 |
| `adapters/ctr_predictor_adapter/baseline_lookup.py` | v3.1 口径文档块（CTR=去重点击/触达成功 + plan 加权 + 不跨渠道 + 不截断），不动现有查询逻辑 | ✅ Phase 6 P2 落 |
| `services/ctr_prediction_service.py` | 顶部 docstring 同步 v3.1 口径注释，函数体不动 | ✅ Phase 6 P2 落 |
| `repositories/feedback_repository.py` | 入库 schema 标注：分子=去重点击人次（`clicks_dedup`）、分母=触达成功（`reach_success`），与 v3.1 对齐；列名保留 `click_count` 不破坏 Phase 5 已上传数据 | ✅ Phase 6 P2 落 |
| `tools/calibrate_baseline.py` | `--definition` flag（默认 `v3.1`），输出 json `definition` 字段，便于校准溯源 | ✅ Phase 6 P2 落 |
| `tests/verify.py §41` | 构造 5 plan 数据：plan 加权 vs record 加权 vs 中位数 数值对比 + bi_dt 取数边界用例（12 点前后判定） | ✅ Phase 6 P2 落 |
| `docs/feedback-ctr.md §3` | 校准机制节加 v3.1 口径引用 + bi_dt 铁律 | � 后续维护补 |

---

## 5. 反哺数据回传机制（已确认）

**沿用 Phase 5 已搭好的批量回灌管道，不做实时对接**：

```
[投放跑完]
   ↓
[数据平台按 v0.2 口径导出一张表 CSV/Excel]
   ↓  列：plan_id / signature / channel / reach_success / clicks_dedup / order_count / sent_date
[pages/05_feedback 上传该表]
   ↓
[入 feedback.db（SQLite）]
   ↓
[系统用 signature 指纹自动配对"当初预测 CTR" vs "本次真实 CTR"]
   ↓
[算准确率：MAE / MAPE，画误差曲线]
   ↓
[calibrate_baseline.py 按新数据重算基准 — 现阶段 L0 EMA 三段策略]
   ↓
[样本累计 ≥ 1000 条后切 L1 GBDT 重训]
```

**关键前提**：导出表的口径必须与本文 §2 Q1-Q6 完全一致，否则回传的"真实值"是另一套定义，模型越学越歪。

### 5.1 上传表格式约束（feedback_service 解析要求）

| 字段 | 类型 | 必填 | 备注 |
|---|---|---|---|
| `signature` 或 `task_signature` | str | ✅ | join 锚点，与 generation_records.signature 对齐；缺失时按 channel+coupon+plan_type+其他维度兜底签 |
| `channel` | str | ✅ | 6 渠道枚举 |
| `reach_success` | int | ✅ | Q2 触达成功 |
| `clicks_dedup` 或 `click_count` 或 `点击` | int | ✅ | Q1 去重点击人次；列名别名兼容 |
| `order_count` 或 `订单` | int | ❌ | 派生转化率用 |
| `coupon` / `plan_type` / `sent_date` | str | ❌ | 维度辅助 |
| `source` / `imported_at` | str | ❌ | 来源 + 导入时间戳 |

详见 `services/feedback_service.py` 列名别名表。

---

## 6. 与决策文档联动（按 §6.2 梯队推进）

| # | 决策项 | 状态 |
|---|---|---|
| #5 | CTR **口径定义** | ✅ v0.2 拍板（本稿） |
| #6 | 反哺**是否影响生成排序**（A/B/C 候选排序） | � 第一梯队，待 #5 走完后启 |
| #3 | CTR 反哺**触发条件**（累计多少 plan / 定时？） | ⏳ 第一梯队，待 #5 走完后启 |
| #1 | 产品与权益 维度枚举 + 是否参与生成 | ⏳ 第二梯队 |
| #2 | 投放目标 维度枚举 + 是否参与生成 | � 第二梯队 |
| #4 | CTR 校准频率（手动 / T+1 / 周） | ⏳ 第二梯队 |
| #7 | 02-05 附属页面**是否纳入正式版** | ⏳ 第二梯队 |

**#5 落地后启 P0/P1 反哺 demo 数据回灌（业务确认前不接真实数据，仅 demo 走通流程）**。

---

## 7. 不在本文范围（明确排除）

- ❌ 反哺**业务排序**（决策文档 #6）—— 另开稿子
- ❌ 反哺**触发条件**（决策文档 #3）—— 另开稿子
- ❌ 反哺**校准频率**（决策文档 #4）—— 另开稿子
- ❌ L1 GBDT 训练细节（特征工程 / 评估指标）—— Handoff §5.5 已写高层

---

## 8. 一句话总结

> **plan 加权 CTR = 去重点击人次 / 触达成功（min_reach ≥ 1000），不跨渠道，不截断，取数按 bi_dt T-1 快照（12 点前用 INTERVAL 2）**——这是 v0.2 业务拍板口径，Phase 6 P2 落到实现。
