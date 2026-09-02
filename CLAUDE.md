# CLAUDE.md — MCD AI 内容运营工作台

> 给 AI 会话看的项目说明。新 session 第一件事：读 `Handoff.md` + `PRD.md` + 本文件。
> 范式：仿 `C:\ideon\mcd-copy-analyzer\CLAUDE.md`（95 行）。

---

## 1. 项目一句话

把 mcd-copy-analyzer（文案分析）+ mcd-ctr-predictor（CTR 预测）+ 新 PRD（AI 文案生成）整合到一个 Streamlit 内网工作台，4 个业务页面共用一套 Adapter 层。

---

## 2. 必读

1. `Handoff.md` — 项目记忆 + 决策 + 复用清单 + 教训（先读）
2. `PRD.md` — 产品需求（重点 §4.0 CTR 三入口 / §13.5 Adapter 策略 / §15.A 工程化配套）
3. `.claude/agents/` 下的 3 个 sub-agent（code-reviewer / integration-helper / test-runner）
4. `data/ctr_baseline.json` — CTR 域事实基础（7 维度 + 元信息）

---

## 3. 架构概览

```
Browser
  ↓
Streamlit (app.py + pages/)
  ↓
services/ (业务层，纯函数为主)
  ├── generation_service       任务输入 → 3 条候选
  ├── copy_analysis_service    内容诊断 / 词频分析
  ├── ctr_prediction_service   CTR Adapter 包装
  ├── similarity_service       TF-IDF 找相似历史 Plan
  ├── rule_engine              规则检查
  ↓
adapters/ (隔离旧项目)
  ├── copy_analyzer_adapter    ← C:\ideon\mcd-copy-analyzer\*.py 纯函数
  ├── ctr_predictor_adapter    ← C:\ideon\mcd-ctr-predictor\ctr_predictor.py 纯函数
  ├── demo_llm_adapter         ← PRD §19 Demo 模式
  ├── internal_llm_adapter     ← 内网 LLM 真实调用
  ↓
core/ (基础层)
  ├── config                   Pydantic Settings + 环境变量
  ├── schemas                  TaskInput / Candidate / PredictionResult dataclass
  ├── exceptions               业务异常
  └── llm_gateway              统一 LLM 调用层（聚合 demo/internal）
  ↓
repositories/ (存储)
  └── sqlite_repository
  ↓
data/ (静态配置)
  ├── ctr_baseline.json        v3.0（7 维度）
  ├── custom_dict.txt          jieba 自定义词典
  ├── stopwords.txt            停用词 + 禁词段
  └── frameworks.json          6 条高 CTR 框架
```

**模块边界**：
- 页面层不得直接拼 Prompt / 调用具体模型 SDK / 保存 API Key / 操作数据库
- 模型调用统一通过 `core/llm_gateway.py`
- 规则检查统一通过 `services/rule_engine.py`
- 存储统一通过 `repositories/sqlite_repository.py`
- 旧项目代码通过 `adapters/` 间接调用，**禁止页面层直接 import 旧项目模块**

---

## 4. 关键约束（违反即出错）

### 4.1 架构红线
- **禁止**页面层 import `mcd-copy-analyzer` 或 `mcd-ctr-predictor`
- **禁止**业务层依赖 `st.session_state`（应通过参数传递）
- **禁止**Prompt / 渠道规则 / 禁用词 写死在 UI 文件
- **禁止**数据库操作散落在页面中
- **禁止**复制整个 `ctr_predictor.py` 或 `app.py` 到新项目
- **禁止**用 `time.sleep` / 随机数包装假预测结果

### 4.2 CTR 结果四态分明
- `model_prediction`：真实调用预测逻辑
- `baseline_only`：只返回历史基准
- `demo`：Demo 数据稳定占位（带"演示数据"标识）
- `unavailable`：无有效结果（必须显示原因）

不允许把 `demo` 或 `baseline_only` 标签写成"预测准确率 77%"。

### 4.3 数据契约
- `ctr_baseline.json` 是 CTR 域事实基础，7 维度结构是契约
- 加新维度必须同步修改 `adapters/ctr_predictor_adapter/baseline_lookup.py` 查找分支
- `OPTIMAL_CHARS` 不再双源维护，统一从 baseline JSON 的 `optimal_chars` 字段读
- `data/frameworks.json` 的 metrics 是快照，需重新生成

### 4.4 测试与验证
- 改核心函数前先跑 `python tests/verify.py`
- 改 Adapter 前先跑 `pytest tests/test_ctr_adapter.py`
  （注：当前 `tests/` 只有 `verify.py`；`test_ctr_adapter.py` 尚未拆分，待 Phase 21 评估）
- 改页面层先启动 `setup_and_run.bat` 验证 demo 模式跑通

---

## 5. 复用清单（旧模块 Adapter 映射）

详见 `Handoff.md` §3。简版：

**从 mcd-copy-analyzer 复用**：
- `data.py` parse_message / _map_columns / build（纯函数）
- `analyzer.py` tokenize / diagnose_score / match_frameworks（脱 Streamlit）
- `ai_service.py` provider + JSON 解析（thin wrapper）
- `config.py` 颜色 token + axis_rate（直接复用）

**从 mcd-ctr-predictor 复用**：
- `get_baseline_ctr` / `get_time_multiplier` / `build_context_for_llm` / `auto_detect*` / `get_char_range`
- `calibrate_baseline.py`（整体搬为离线工具）
- `tests/verify.py` 模式（升级为解耦版）

**不复用**：
- mcd-copy-analyzer 的 `app.py`（强耦合 Streamlit）
- mcd-copy-analyzer 的 `inject_css`（项目特定 hack）
- mcd-ctr-predictor 的 `styles.py`（仅参考设计）

---

## 6. Provider 配置

### 6.1 应用模式（`APP_MODE`）
- `demo`：无外部 API 也能跑（默认）
- `internal_llm`：调用内网 LLM 网关

### 6.2 CTR 模式（`CTR_MODE`，独立于 APP_MODE）
- `existing_predictor`：调用 ctr_predictor 真实预测
- `baseline_only`：只返回历史基准
- `demo`：Demo 数据稳定占位
- `l1_model`：L1 LightGBM 回归（Phase 20，业务主动切主流程）
- `unavailable`：不返回 CTR 结果

### 6.3 LLM Provider（OpenAI 兼容协议）
- `openai` / `siliconflow` / `qianfan` / `MiniMax`
- 通过 `.env` 的 `LLM_PROVIDER` / `LLM_MODEL` / `LLM_BASE_URL` / `LLM_API_KEY` 配置
- 限速：`LLM_BATCH_SLEEP=1.2`（ctr-predictor 经验值）
- 超时：`LLM_TIMEOUT=60`

---

## 7. 关键命令

```bash
# 启动（双击或命令行）
setup_and_run.bat

# 手动启动
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py

# 测试
python tests/verify.py                    # 无 pytest 依赖
python -m pytest tests/                   # 单元测试

# 校准 baseline（离线工具）
python tools/calibrate_baseline.py

# 端口冲突时（默认 8510；旧项目各占 8501）
STREAMLIT_PORT=8511 streamlit run app.py
```

---

## 8. Self-check（每次改动前）

- [ ] 改 Adapter 是否影响 `mcd-copy-analyzer` 或 `mcd-ctr-predictor` 的独立运行？
- [ ] 改页面是否破坏了 PRD §3.1 保留的领导 Demo P0 清单？
- [ ] 改 CTR 相关是否正确标记四态 result_type？
- [ ] 改 baseline JSON 是否同步修改了 baseline_lookup 的查找分支？
- [ ] 新增维度 / 渠道 / 字段是否在 `config/` 或 `data/` 配置文件而非硬编码？
- [ ] **Phase 收尾必同步 `Handoff.md`**：§6 待办列表状态 / §9 用例数 / §10 Self-check 清单（2026-08-26 起强制；防入口信息过期误导下个 AI）

---

## 9. 注意事项

- **UI 不放 emoji**（沿用 mcd-copy-analyzer / mcd-content-rank 风格）
- **沟通全中文**（业务方是麦当劳内部团队）
- **列名一律"触达成功"**（避免和"预计触达"混淆）
- **CTR 一律 plan 加权**（不记录级平均）：`sum(点击) / sum(触达成功)`
- **样本量透明**：每词对比显示 `n_plans + n_records + 触达数`，UI 标"高频伴随 ≠ 导致"
- **默认 `min_plans=3`**，plan<5 加预警

---

## 10. 快速上手示例

**新增一个业务页面**（如 §4 扩展页面 5）：

1. 在 `pages/` 下建 `05_xxx.py`
2. 在 `services/` 下建 `xxx_service.py`（纯函数 + dataclass）
3. 如需旧项目能力，在 `adapters/` 加 adapter，service 层调用
4. 写 `tests/test_xxx.py`（pytest）+ 在 `tests/verify.py` 加用例
5. 更新 `Handoff.md` §3 复用清单 / §9 待办 / §10 Self-check
6. 跑 `setup_and_run.bat` 验证 demo 模式

**新增一个渠道规则**：

1. 在 `config/channel_rules.yaml` 加渠道定义（title_max_length / body_max_length / require_title）
2. 在 `services/rule_engine.py` 检查读取配置
3. 写测试用例（边界值）
4. 更新 PRD §26 待确认项（如有未确认字段）
