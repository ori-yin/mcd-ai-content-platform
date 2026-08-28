# mcd-ai-content-platform — 待办与候选（详）

> **何时读我**：开新 Phase 前扫这里，看哪些待办可顺手清掉 / 哪些候选已被否决。
> 索引在 `Handoff.md` §6.2/§6.3 + 本文件目录。

---

## 目录

- [§6.2 待业务确认（按返工风险梯队）](#62-待业务确认按返工风险梯队)
- [§6.3 候选（详 §5.5 CTR Roadmap）](#63-候选详-55-ctr-roadmap)

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
- [ ] **#4** CTR 校准频率（手动 / T+1 / 周）
- [ ] **#7** 02-05 附属页面**是否纳入正式版**（含字典维护 UI `pages/06_settings.py` 议题）

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

**业务确认后启动**（下方 2 项候选 L1 + P4 待业务拍板；§6.3 原 P3 维度权重动态 + demo 数据回灌已在 Phase 6 P4 完成，见 §5）。

#### L1 · LightGBM 回归替 baseline 查找表（详 §5.5）✅ **Phase 18 已落地（2026-08-28）**

> **用户拍板"先试试看"**（2026-08-28），基于历史 CNN 4.4 万行数据直接训练。详见下方"Phase 18 L1 LightGBM PoC"段。下方为原 §5.5 设计稿，实际落地配置按 PoC 结果（剔除小程序 + 高效词 + 时间衰减）。

**一句话**：用 LightGBM 回归替 baseline 7 维查表，**结构化特征 + 中样本 + 可解释**三场景适配 GBDT，DNN 是过度设计。

**为什么是 GBDT 不是 DNN**：
- 输入 = 结构化表格（7 维 + 字数 + emoji + 命中词），不是文本/图像
- 样本 = 几千到几万（麦当劳业务体量），不是亿级
- 可解释 = 刚需——业务问"为什么这个 Plan CTR 高"，GBDT 出特征重要性，DNN 给一堆注意力
- DeepFM/DIN/Transformer 要亿级样本回本，喂不饱

**关键设计点**：
- **特征 X**：7 维基础 + 文本衍生（title_len/body_len/emoji_count/命中词数）+ 历史衍生（past_ctr_similar）+ 时段衍生（dayofweek/hour/is_holiday）
- **训练集**：feedback.db（真实 CTR）按 signature join records.db → 每个 plan 一行 (X, y)
- **样本阈值**：< 50 plan 走 baseline / 50-500 走 L0 EMA / **~ 1000 切 L1**（< 1000 易过拟合，叶节点多 + 噪声大）
- **离线回测门禁**：L1 MAE > L0 × 1.05 → 拒绝上线，回退 L0
- **冷启动兜底**：新维度组合 L1 也查不到，走 baseline 兜底（4 态分明不变）
- **误差曲线**（必备）：预测 vs 真实 MAE/MAPE 散点 + 时间趋势图；曲线往下 = 在学，平/往上 = 漂移触发告警

**落地步骤**（粗估 10 工作日）：
1. `tools/train_l1_model.py`（~150 行：加载 feedback.db → join → 训练集 → LightGBM 训练 → 保存 .pkl）
2. `adapters/ctr_predictor_adapter/l1_predictor.py`（~50 行：加载 .pkl + predict）
3. `CTRPredictionAdapter` mode 加 `"l1_model"`（~30 行）
4. `tools/plot_error_curve.py`（~80 行：每周预测 vs 真实 MAE 散点图）
5. `tests/verify.py §43` L1 模块（~10 用例）
6. 业务反馈：误差曲线图、特征重要性 Top10、模型切换门禁报告

**风险**：
1. **过拟合**：< 千条样本时 GBDT 不如 L0 EMA
2. **冷启动**：新维度组合必须走 baseline 兜底
3. **误差曲线不一定往下走**——可能持平或上漂，这是诊断信号（"在学" vs "漂移"）
4. **责任划分**：谁负责训练 / 谁负责监控 / 谁有权批准上线

**业务要拍 4 项**：
1. ✅ **切 L1 时点**：用户主动（sidebar selectbox 切到 l1_model 即可）—— Phase 20 已落地
2. ⏳ **谁来训练**：业务方跑 / 平台自动 / 数据团队跑？ → 待业务拍板
3. ✅ **误差告警阈值**：MAE 涨到 baseline × 1.3 触发告警 —— Phase 20 `tools/monitor_l1_drift.py` 已落地（建议 30%，工具参数可调 `--alert-ratio`）
4. ⏳ **可解释输出**：要不要把"特征重要性 Top10 维度"每周给业务看？ → 待业务拍板

**Phase 19 完成项（2026-08-28）**：
- ✅ `adapters/ctr_predictor_adapter/l1_predictor.py` 接入生产（predict_l1 / predict_l1_batch / predict_l1_status）
- ✅ `__init__.py` 导出 4 符号
- ✅ 静默双轨：`pages/01_content_studio.py` sidebar admin 开关，默认关
- ✅ 4 态分明：model / baseline_only（模型缺）/ unavailable（渠道不在训练范围 + 特征构造失败）
- ✅ 渠道校验：L1_SUPPORTED_CHANNELS = (APP Push, 企微1v1, 短信)
- ✅ 容错：lru_cache 加载 + 异常路径静默降级（不抛错影响主流程）
- ✅ 验证：verify 655 → 677 PASS（§56 新增 22 用例）

**Phase 20 完成项（2026-08-28）**：
- ✅ `CTRPredictionAdapter.VALID_MODES` 加 `"l1_model"`（5 态：existing_predictor/baseline_only/demo/l1_model/unavailable）
- ✅ `_l1_model_pred` 走 predict_l1 → 4 态透传（model→model_prediction/source=l1_lightgbm，baseline_only→baseline_only，unavailable→unavailable）
- ✅ `pages/01_content_studio.py` sidebar "CTR 主流程模式" selectbox（demo/baseline_only/l1_model，默认 demo，env CTR_MODE 可覆盖）；L1 模型缺失时 l1_model 不可选
- ✅ `tools/monitor_l1_drift.py` records.db join feedback.db → MAE vs baseline → 1.3x 告警 + drift_log.csv 留档
- ✅ 验证：verify 677 → 697 PASS（§57 新增 20 用例）

**Phase 19+20 未做（留给后续 Phase）**：
- ⏳ 训练责任人 + 重训调度机制
- ⏳ `tools/print_feature_importance.py` 特征重要性 Top10 周报
- ⏳ CTRPredictionAdapter mode 切主流程的回滚机制（万一 L1 漂移自动回退 demo）

---

#### P4 · 历史洞察签名关联（04 七 Tab 加 signature 视角）

**一句话**：把"哪条 Plan 后来效果如何"接进洞察 Tab，让业务闭环"看"反哺。

**当前状态**：`pages/04_historical_insights.py` 七 Tab 按 plan / 文案维度统计，没有"采纳后真实效果"视角。P4 加 signature 视角 = 新增第 8 Tab"签名关联"。

**为什么重要**：
- 闭环到"看"——业务验证"我推荐的文案投出去后真有人点吗"
- 反哺闭环可视化——哪些文案被采纳 → 投出去 → 真实 CTR 多高
- 找高效 Plan 模板——相似文案 vs 真实 CTR 找规律

**Tab 内容**：
- 表格按 signature 分组聚合：`signature` / `采纳数` / `预测 CTR 平均` / **feedback 接入后**加 `真实 CTR 中位数/P90` / `预测 vs 真实 diff`
- 散点图：预测 CTR (x) vs 真实 CTR (y)，每点一个 plan
- Top10 复用模板：采纳数最多的 signature

**数据来源**：
```
records.db    feedback.db
   ↓              ↓
   selected_id ←─signature─→ 真实 CTR（按 signature join）
```

没有 feedback 数据时只能看"采纳数"，无法做 CTR 对比——这正是当前状态。

**风险**：
1. **没数据时空着**——业务确认前不接真实数据，Tab 加了但只能看采纳数，可能觉得"没用"
2. **数据稀疏**——单 signature 可能只 1-2 个 plan，"中位数 CTR"无意义；加阈值保护（≥ N 才显示 CTR 列）
3. **混淆"采纳"和"成功"**——selected_id ≠ 投放成功，只是"运营最终选的那条"
4. **CTR 散点少时画不出**——feedback 样本 < 50 时散点只有几个点，无诊断价值
5. **与 L1 联动**——L1 训练数据正是"signature + 真实 CTR"，P4 是 L1 的"查看界面"

**落地步骤**（粗估 3 工作日）：
1. `services/signature_insight_service.py`（~100 行）
   - `summarize_signatures(records, feedback)` → `list[{signature, count, pred_ctr_avg, real_ctr_median}]`
   - 空数据兜底：`feedback is None` → 只返回采纳数维度
2. `pages/04_historical_insights.py` 加第 8 Tab（~80 行 + plotly 散点）
3. `tests/verify.py §43`（~6 用例：聚合、join、空数据兜底、稀疏过滤）
4. **联动 L1**：`signature_insight_service` 直接给 `train_l1_model.py` 提供训练数据

**业务要拍 4 项**：
1. **要不要加这个 Tab**：业务确认前不接真实数据，Tab 加了只能看采纳数——值不值得？
2. **CTR 列显示阈值**：feedback 样本 ≥ 多少才显示 CTR 列？建议 ≥ 50
3. **展示粒度**：signature（细 12 位指纹）vs strategy（A_核心利益直给 3 选 1）？
4. **与 L1 联动**：要不要 P4 先于 L1 做（先有"看"再有"用"）？

**建议节奏**：P4 先做（3 天）→ L1 后做（10 天）。先有"看"的能力，再上"用"的模型。

---

#### UI · 整体重设计（候选 · 2026-08-28 find-skills 调研）

**用户反馈（2026-08-28）**：核心逻辑（Phase 19-21 L1 主流程 + simplify 清理）已完成，**UI 太丑，整体架构 + 布局都有大问题**。下一步计划整体重构，不是修修补补。

**find-skills 调研结论**（2026-08-28）：

**已装可直接用**（`~\.claude\skills\`）：
- `developing-with-streamlit` —— **最对口**，Streamlit 官方，覆盖 dashboards / themes / layouts / 自定义组件 / 美化主题 / 性能
- `frontend-design` —— 通用前端设计
- `designing-beautiful-websites` —— 通用网站美化

**skills.sh 命中度高**（待评估装不装）：
| Skill | installs | 备注 |
|---|---|---|
| `vercel-labs/agent-skills@web-design-guidelines` | **584.6K** ⭐ | 通用 web 设计准则（Vercel/Next 背景） |
| `nextlevelbuilder/ui-ux-pro-max-skill@ckm:design-system` | 32.8K | UI/UX 设计系统（通用） |
| `firecrawl/firecrawl-workflows@firecrawl-dashboard-reporting` | 31.1K | dashboard 报告 |
| `wshobson/agents@kpi-dashboard-design` | 13.3K | KPI dashboard 设计 |

**SkillHub 国内源**：`skillhub: command not found`（CLI 未装），按 memory `install_skills.md` 应补装后同步搜国内源。

**下一步行动**：
1. 先跑 `python "C:/Users/a952462/.claude/skills/developing-with-streamlit/scripts/discover.py" --project-dir "C:/ideon/mcd-ai-content-platform"` 拿项目级 recommendations
2. 按 discover.py 输出决定要不要补装 `vercel-labs/agent-skills@web-design-guidelines`（设计规范通用补充）或 `ui-ux-pro-max-skill@design-system`（设计系统）
3. 选定 skill 后整体重构（CLAUDE.md §9 红线 + 走 skill 流水线，不自己糊 CSS）
4. Streamlit UI 改动注意 `feedback-streamlit-ui-iteration` 4 个常见坑（清理列表冲突、类名冲突、注入 DOM 不归 React 管、CSS 时序）

**作用域**：当前页面 6 个（app + 00-05）+ 顶部 banner 系统 + sidebar 主题；**不动后端逻辑**（已稳定，Phase 19-21 验证 697 PASS）。

---

