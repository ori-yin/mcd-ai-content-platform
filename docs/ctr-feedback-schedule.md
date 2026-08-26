# CTR 反哺 · 触发条件与执行节奏（2026-08-26 业务拍板）

> 对应 Handoff §6.2 第一梯队 #3——CTR 反哺**触发条件**拍板。
> 配套文档：`docs/ctr-kpi-definition-proposal-v0.2.md`（口径 v3.1）+ `docs/feedback-ctr.md`（反哺思考笔记）

## 一句话

**每周一上午手动跑一次 `tools/calibrate_baseline.py`**——节奏稳定、人可控、不漂移、阻塞感低。

## 为什么是手动一周一次

| 维度 | 评估 |
|---|---|
| **人可控** | 业务确认前不接实时回流，手动节奏避免口径返工 |
| **节奏稳定** | 漏一周 = 空一周；固定每周一同一天，可设日历提醒 |
| **不漂移** | 不做实时自动校准——baseline 滞后一周，CTR 突变场景（促销/换季）响应慢，但**接受这个代价换稳定性** |
| **阻塞感低** | 业务方每周只需要：① 上传上周真实 CSV/Excel → ② 跑一次脚本 → ③ 看 diff 报告 |

## 执行流程（每周一上午，~5 分钟）

```
1. 打开 pages/05_feedback（或直接命令行）
   上传上周真实投放 CSV/Excel → 写入 data/feedback.db

2. 跑校准：
   python tools/calibrate_baseline.py --db data/feedback.db

3. 看输出：
   - 渠道维度：T-1 → T+7 的 CTR diff
   - 渠道×用券维度：同上
   - 跳过提示：n_plans<5 跳过（保留旧 baseline）

4. 校对结果：
   - data/ctr_baseline_v3.x.json：新版本（v3.x → v3.x+1）
   - data/ctr_baseline_v3.x.json.bak：旧版本备份
   - diff 报告：终端输出已打印
```

## 跳过条件（防过拟合）

**沿用 Phase 5 P2 的 `_calibrate_value` 三段策略**：

| n_plans（累计 plan 数） | 策略 | 行为 |
|---|---|---|
| **< 5** | 跳过 | 保留旧 baseline，提示"样本不足" |
| **5 ≤ n_plans < 20** | 指数滑动 α=0.3 | 新数据 30% 权重 + 旧数据 70% |
| **≥ 20** | 全量覆盖 α=1.0 | 完全用新数据 |

**铁律**：哪怕只有 1 个 plan 也不要用它覆盖 baseline——CTR 方差极大，单 plan 会拉偏。

## 漏周策略

- **漏 1 周**：当周 baseline 保持不变，下周合并 2 周数据正常跑
- **漏 ≥ 2 周**：累积 ≥ 3 周数据时 n_plans 容易越过 20 → 全量覆盖；**业务方自己心里有数就行**，无需特殊处理
- **业务方主动补**：周一忘了可以周二/周三跑——节奏不是强约束

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