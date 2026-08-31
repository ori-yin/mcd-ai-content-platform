# L1 LightGBM 模型 · 训练与运维 Runbook

> L1 = LightGBM 替 baseline 查找表（Phase 18 PoC + Phase 19/20 入生产 + Phase 22 C 漂移自动回退 + Phase 24 sweep 确认 live，2026-08-28）。
> **责任人：用户自己**（手动跑，无自动调度，2026-08-31 拍板）。

---

## 一句话

**训练按需 + 监控每月 + 月报月初 + 漂移告警自动回退（无需介入）**。

---

## 5 步流程

### 1️⃣ 重训模型（按需）

**何时跑**（满足任一）：
- baseline 反馈累积 ≥ 1000 plan 时（Phase 16.5 拍板：< 1000 易过拟合）
- 漂移监控告警持续（baseline_only 还不够准）
- 业务侧新维度加入（新增渠道 / 新字段）
- 季度复盘（不强约束）

**命令**：
```bash
python tools/train_lgbm.py \
    --data data/cnn_backup_cleaned.xlsx \
    --model-out data/lgbm_model_v1.pkl \
    --meta-out data/lgbm_feature_meta.json
```

**输出**：
- `data/lgbm_model_v1.pkl`（LightGBM 模型）
- `data/lgbm_feature_meta.json`（15 特征 + test_metrics + plan_type_te_map）
- terminal 打印 overall MAE / per-channel / per-bucket

**跑后必看 3 项**：
1. `overall_mae_pct` ≤ 0.5%（vs 上次涨 > 30% = **退步，不要上线**）
2. APP Push / 企微1v1 / 短信 三渠道 MAE **全 ≤ baseline × 1.05**
3. test R² ≥ 0.05（Phase 18 是 0.0806，新模型不能低太多）

**L1 vs L0 同口径对比**（强制，不对比不能上线）：
```bash
python tools/evaluate_lgbm.py \
    --model data/lgbm_model_v1.pkl \
    --meta data/lgbm_feature_meta.json \
    --baseline data/ctr_baseline.json \
    --data data/cnn_backup_cleaned.xlsx
```
- 三渠道 L1 **全胜** → 进第 2 步
- 有一渠道 L0 胜 → 保留旧模型，**不上线**

---

### 2️⃣ 切到 L1（admin）

**前提**：第 1 步通过。

**操作**：
1. 开 `01 内容创作` 页面
2. sidebar "CTR 主流程模式" selectbox：选 `l1_model`
3. 看 L1 加载状态：✅ = 已切；❌ = 模型文件缺失，去排查
4. 模型不健康或漂移告警 → `monitor_l1_drift.py` 已自动写 `data/active_mode.txt` 强制回退，开 01 会显示**黄色 banner "已被自动回退到 {mode}（漂移告警）"**

---

### 3️⃣ 监控漂移（每月手动）

**何时跑**：每月校准 baseline 后 1-2 天（与 calibrate_baseline 同节奏）。

**命令**：
```bash
python tools/monitor_l1_drift.py --min-real-reach 50
```

**输出解读**：

| 状态 | 触发条件 | 自动动作 |
|---|---|---|
| **OK** | MAE ≤ baseline × 1.3 | 绿灯，清空 `data/active_mode.txt` |
| **WARN** | baseline × 1.3 < MAE ≤ baseline × 2.0 | 黄灯，写 `active_mode.txt = baseline_only` |
| **ALERT** | MAE > baseline × 2.0 | 红灯，写 `active_mode.txt = demo` |

漂移日志落档 `data/drift_log.csv`。

**人工处理**（WARN / ALERT 后）：
1. **先看 baseline 是否校准晚了**——跑 `python tools/calibrate_baseline.py --db data/feedback.db` 重算 baseline，再重跑监控
2. 仍告警 → 回第 1 步重训模型
3. **不要手动改 `active_mode.txt`**——改完下次监控会覆盖

---

### 4️⃣ 自动回退（无需介入）

`tools/monitor_l1_drift.py` 已集成 `apply_auto_rollback`：
- ALERT → 写 `data/active_mode.txt = demo`
- WARN → 写 `data/active_mode.txt = baseline_only`
- OK → 清除文件

`pages/01_content_studio.py` 启动时读 `data/active_mode.txt` → 覆盖 sidebar 默认 `ctr_mode` + 黄色 banner 提示。

**人工恢复**（漂移解决后想切回 L1）：
```bash
rm data/active_mode.txt
```
下次开 01 恢复 sidebar 默认（demo），手动切回 `l1_model`。

---

### 5️⃣ 月报（月初）

**何时跑**：每月 1 号上午（与 calibrate_baseline / monitor 同节奏）。

**命令**：
```bash
python tools/print_feature_importance.py --top 10 --importance-type gain
```

**输出**：
- terminal 打印 Top10 + 涨/跌标（与上月快照对比，±2 名次算涨/跌）
- 落档 `data/feature_importance_history/importance_YYYY-MM-DD_HHMMSS.json`
- 落档 `data/reports/feature_importance_YYYY-MM-DD.txt`

**必看 5 项**：
1. **Top 5 维度稳定性**（无 ±2 名次变化 = 模型稳定，不再"在学"）
2. **高效词命中数占比**（下滑 = 文案命中高效词趋势弱化）
3. **渠道相关特征占比**（L1 过度依赖渠道 = 警惕过拟合，应回到 baseline × tm）
4. **标题字数 vs 正文长度 占比**（Phase 18 基线 22.92% vs 35.19%，大幅变化 = 数据分布漂移）
5. **计划类型 TE 占比**（AARRPlan vs 常规Plan 区分度，弱化 = 维度失效）

**用户口径**：月报自己看为主，不分享业务部（2026-08-28 拍板）。

---

## ⚠️ L1 不支持的渠道

L1 仅在以下 3 个渠道训练过：
- **APP Push**
- **企微1v1**
- **短信**

其他渠道（微信小程序订阅消息）切 L1 → 自动降级 `unavailable`，主流程走 baseline_lookup，不报错。

---

## 关键路径速查

| 路径 | 用途 |
|---|---|
| `tools/train_lgbm.py` | 重训模型 |
| `tools/evaluate_lgbm.py` | L1 vs L0 同口径对比 |
| `tools/monitor_l1_drift.py` | 漂移监控 + 自动回退 |
| `tools/print_feature_importance.py` | 月报 |
| `data/lgbm_model_v1.pkl` | 模型文件（169 KB） |
| `data/lgbm_feature_meta.json` | 15 特征元信息 |
| `data/active_mode.txt` | 自动回退状态（drift 触发时写） |
| `data/drift_log.csv` | 漂移历史日志 |
| `data/feature_importance_history/*.json` | 月报快照（89 个） |
| `data/reports/feature_importance_*.txt` | 月报文本 |

---

## 相关决策

- `Handoff.md §6.1 Phase 18`：L1 PoC 训练（剔除小程序 + 14→15 特征 + 时间衰减）
- `Handoff.md §6.1 Phase 19`：L1 入生产 + 静默双轨
- `Handoff.md §6.1 Phase 20`：l1_model mode 主流程接入 + 漂移监控
- `Handoff.md §6.1 Phase 22 B`：特征重要性月报脚本
- `Handoff.md §6.1 Phase 22 C`：漂移自动回退
- `Handoff.md §6.1 Phase 24`：全量 sweep 确认 L1 live
- `Handoff-todo.md §6.3 L1`：业务拍板 4 项（2026-08-31 全部 ✅）
