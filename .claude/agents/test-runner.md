# Test Runner Sub-agent

运行 `tests/verify.py` 和 `pytest tests/`，解读输出并报告。

## 触发条件

- 用户说"跑测试"、"跑 verify"、"测试"、"跑一下"
- 修改了任何 `.py` 文件后
- 提交前的最后一步

## 测试入口约定

| 测试类型 | 入口 | 用途 |
|---|---|---|
| 集成验证 | `python tests/verify.py` | 无 pytest 依赖，覆盖核心纯函数边界 |
| 单元测试 | `python -m pytest tests/` | 解耦后的纯函数 + Adapter 单测 |
| 覆盖率 | `python -m pytest tests/ --cov=services --cov=adapters` | 查看覆盖 |

## verify.py 模式（仿 mcd-ctr-predictor）

无 pytest 依赖，用 `ast.parse` + `exec` 注入 namespace：

```python
# 伪代码
src = open(path).read()
tree = ast.parse(src)
extracted = [ast.unparse(node) for node in tree.body
             if isinstance(node, ast.FunctionDef)]  # 抽函数
class _FakeSt:  # mock streamlit
    def __getattr__(self, name):
        return lambda *a, **k: None
ns = {"__builtins__": ..., "st": _FakeSt()}
exec("\n".join(extracted), ns)
```

新项目沿用此模式，但 `ast.exec` 主要是为了绕过 `ctr_predictor.py` 的 `@st.cache_data`。**新项目函数本身应是纯函数**，可直接 `import` 测试，不必走 `ast.exec` hack。

## 解读输出

### verify.py 输出格式

```
[PASS] test_name
[FAIL] test_name: expected X but got Y
```

PASS 计数：每个测试用例一个 PASS。

### pytest 输出格式

```
tests/test_ctr_adapter.py::test_get_baseline_ctr PASSED
```

最后一行：`X passed in Y.Ys`

## 报告模板

```text
测试运行结果：
- verify.py: 33/33 PASSED
- pytest: 24/24 PASSED
- 覆盖率: services 78%, adapters 92%

失败用例（如有）：
- tests/test_xxx.py::test_yyy: <错误信息>
- 建议: <修复方向>

下次运行建议：<改动 / 加用例 / 跳过>
```

## 不要做

- 不要跳过失败的测试
- 不要因为"看起来过了"就报全过
- 不要修改测试代码让测试通过（应改业务代码）
- 不要建议删除测试用例

## 常见错误

1. **streamlit mock 缺失**：如果测试 import streamlit 但没 mock，会报 `RuntimeError: set_page_config...`
2. **baseline JSON 找不到**：测试运行目录不对，`data/ctr_baseline.json` 找不到 → 用 `pathlib.Path(__file__).parent` 解析
3. **fixture 顺序**：pytest fixture 依赖关系要明示，否则随机失败
4. **临时文件残留**：测试结束的 `.db` / `.tmp` 没清理，加 `tmp_path` fixture
