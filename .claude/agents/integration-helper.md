# Integration Helper Sub-agent

指导如何把 mcd-copy-analyzer / mcd-ctr-predictor 的能力集成到 mcd-ai-content-platform。

## 触发条件

- 用户说"集成"、"接入"、"调用"、"复用"、"import 旧模块"
- 修改了 `adapters/` 下的文件
- 新增了一个旧模块的 wrapper

## Adapter 策略（PRD §13.5）

### 策略 1：优先直接 import 纯函数

适用于：`mcd-ctr-predictor/ctr_predictor.py` 的 `get_baseline_ctr` / `get_time_multiplier` / `build_context_for_llm` / `auto_detect` / `get_char_range` 等。

操作：
1. 确认函数是纯函数（无 `st.*` 调用，无全局状态读写）
2. 在 `adapters/ctr_predictor_adapter/<name>.py` 中 `from ctr_predictor import <func_name>`
3. 把模块级常量（如 `BASELINE`）改为显式参数注入
4. 加 type hints 和 docstring
5. 写 `tests/test_ctr_adapter.py` 单测

### 策略 2：thin wrapper 抽纯函数

适用于：`mcd-copy-analyzer/analyzer.py`（强依赖 `@st.cache_data`）等。

操作：
1. 识别原函数中所有 `@st.cache_data` 装饰器
2. 把 cache 抽到 `adapters/cache_adapter.py`（用 `functools.lru_cache` 或自定义 key）
3. 业务函数保持纯函数形态
4. UI 层如有需要可在 `ui/cache.py` 重新加 `@st.cache_data`（仅 Streamlit 用）

### 策略 3：复一份配置文件

适用于：`ctr_baseline.json` / `custom_dict.txt` / `stopwords.txt` / `frameworks.json`。

操作：
1. `cp` 一份到新项目 `data/`
2. 不创建符号链接（避免双向耦合）
3. 在 Handoff.md §3.2 标记来源
4. 修改 baseline 时不影响旧项目；旧项目更新时手动同步

### 策略 4：从零实现

适用于：mcd-copy-analyzer 的 `advanced.py` 缺失的 4 个分析（高效 plan / 相似 plan / 每日趋势 / Owner 对比）。

操作：
1. 在 `services/analytics/` 下建独立模块
2. 输入输出契约清晰（参考 Explore agent 报告 §四 接口契约）
3. 写测试 + 加 `Handoff.md` §9 待办标记

## 不要做

- 不要复制整个 `app.py` 或 `ctr_predictor.py` 到新项目
- 不要在 adapter 里改旧项目代码（用 thin wrapper 替代）
- 不要用相对路径 `../../mcd-copy-analyzer/`（用 `import mcd_copy_analyzer` 或 `sys.path.insert`）
- 不要把旧项目的 `@st.cache_data` 直接搬过来

## 验证清单

每次集成新能力后：

- [ ] 旧项目（mcd-copy-analyzer / mcd-ctr-predictor）仍可独立启动
- [ ] 新项目通过 adapter 调用正常
- [ ] `tests/verify.py` 全过
- [ ] `pytest tests/` 全过
- [ ] `python -m py_compile $(git ls-files '*.py')` 全过

## 常见错误

1. **模块级 BASELINE 全局变量**：ctr_predictor.py 的 `BASELINE = json.load(...)` 是模块级，新项目必须改成函数参数
2. **`@st.cache_data` 在新项目没 Streamlit 时报错**：剥掉装饰器，改用 `functools.lru_cache`
3. **`from . import` 相对路径问题**：跨项目 import 用 `sys.path.insert` 或 `pip install -e`
4. **文件名冲突**：`data.py` 与 stdlib `data` 不冲突，但 `random.py` / `os.py` 会冲突，避开
5. **编码问题**：JSON 文件含中文，确保 `encoding="utf-8"`；CTR predictor 的 baseline 是 utf-8 无 BOM
