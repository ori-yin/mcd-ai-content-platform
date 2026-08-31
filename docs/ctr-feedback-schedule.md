# CTR 反哺 · 触发条件与执行节奏

> **2026-08-26 拍板（每周一上午）→ 2026-08-31 用户会话改月度手动**。
> 对应 Handoff §6.2 第一梯队 #3 + 第二梯队 #4——CTR 反哺**触发条件 + 校准频率**拍板。
> 配套文档：`docs/ctr-kpi-definition-proposal-v0.2.md`（口径 v3.1）+ `docs/feedback-ctr.md`（反哺思考笔记）+ `docs/l1-training-runbook.md`（L1 月度同步流程）

## 一句话

**每月 1 号上午手动跑一次 `tools/calibrate_baseline.py`**（旧版：每周一上午，2026-08-31 改月度）——节奏稳定、人可控、不漂移、阻塞感低。

## 为什么是手动月度

| 维度 | 评估 |
|---|---|
| **人可控** | 业务确认前不接实时回流，手动节奏避免口径返工 |
| **节奏稳定** | 漏一月 = 空一月；固定每月 1 号同一天，可设日历提醒 |
| **不漂移** | 不做实时自动校准——baseline 滞后一月，CTR 突变场景（促销/换季）响应慢，但**接受这个代价换稳定性** |
| **阻塞感低** | 用户每月只需要：① 上传上月真实 CSV/Excel → ② 跑一次脚本 → ③ 看 diff 报告 → ④ 跑 `tools/monitor_l1_drift.py` 检查 L1 漂移 |

## 执行流程（每月 1 号上午，~5 分钟）

```
1. 打开 pages/05_feedback（或直接命令行）
   上传上月真实投放 CSV/Excel → 写入 data/feedback.db

2. 跑校准：
   python tools/calibrate_baseline.py --db data/feedback.db

3. 看输出：
   - 渠道维度：上月 vs 上上月的 CTR diff
   - 渠道×用券维度：同上
   - 跳过提示：n_plans<5 跳过（保留旧 baseline）

4. 校对结果：
   - data/ctr_baseline.json：新版本（version 字段 +1；文件名无版本后缀）
   - data/ctr_baseline.bak.json：旧版本备份
   - diff 报告：终端输出已打印

5. （如已切 L1）跑漂移监控：
   python tools/monitor_l1_drift.py --min-real-reach 50
   OK 继续 / WARN/ALERT → 详 docs/l1-training-runbook.md §3 人工处理
```

## 跳过条件（防过拟合）

**沿用 Phase 5 P2 的 `_calibrate_value` 三段策略**：

| n_plans（累计 plan 数） | 策略 | 行为 |
|---|---|---|
| **< 5** | 跳过 | 保留旧 baseline，提示"样本不足" |
| **5 ≤ n_plans < 20** | 指数滑动 α=0.3 | 新数据 30% 权重 + 旧数据 70% |
| **≥ 20** | 全量覆盖 α=1.0 | 完全用新数据 |

**铁律**：哪怕只有 1 个 plan 也不要用它覆盖 baseline——CTR 方差极大，单 plan 会拉偏。

## 漏月策略

- **漏 1 月**：当月 baseline 保持不变，下月合并 2 月数据正常跑
- **漏 ≥ 2 月**：累积 ≥ 2 月数据时 n_plans 容易越过 20 → 全量覆盖；**用户自己心里有数就行**，无需特殊处理
- **主动补**：1 号忘了可以 2 号/3 号跑——节奏不是强约束

## 校准后看什么

**关键 3 个数字**：

1. **新 baseline 的渠道维度 CTR**——和上周对比，平均变化应 ≤ 1 个百分点
2. **n_plans 计数**——上周新增多少 plan？如果 = 0，可能是上传出了问题（feedback.db 没新增）
3. **被跳过的维度**——n_plans<5 的渠道应该很少；大量跳过说明样本分布不均

## 不做什么

- ❌ **不做实时自动校准**——口径返工风险
- ❌ **不做 T+1 校准**——业务方手动一周一次足以
- ❌ **不做 A/B 切换**——v3.1 Q5 已回退到 min_reach>=1000 兜底，等标注机制就位再切 A
- ❌ **不接真实回流**（业务确认前）——保持"演示口径"

## 相关文件

| 路径 | 用途 |
|---|---|
| `tools/calibrate_baseline.py` | 校准主脚本（含 `--db` / `--min-reach` / `--definition` / `--dry-run`） |
| `tools/weekly_calibrate.bat` | 一键执行包装（windows） |
| `data/feedback.db` | 真实投放回流 SQLite（pages/05_feedback 上传） |
| `data/ctr_baseline_v3.x.json` | 校准输出（版本号 +1） |
| `docs/ctr-kpi-definition-proposal-v0.2.md` | v3.1 口径拍板稿 |