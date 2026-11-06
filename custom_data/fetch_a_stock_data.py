import os, json, re, requests, pandas as pd

# 1. 从 SKILL.md 中提取并执行内嵌的 Python 代码
skill_path = os.path.join(os.path.dirname(__file__), "SKILL.md")
with open(skill_path, "r", encoding="utf-8") as f:
    skill_content = f.read()

# 匹配所有 ```python ... ``` 代码块
code_blocks = re.findall(r"```python\n(.*?)```", skill_content, re.DOTALL)
exec_globals = {}
for code in code_blocks:
    exec(code, exec_globals)

# 2. 调用 a-stock-data 的函数（函数名请根据 SKILL.md 实际内容调整）
# 例如获取指数数据（可能叫 get_indices, tencent_index 等，请搜索 SKILL.md 确认）
market_data = {}
try:
    # 示例：假设函数名为 get_indices
    if "get_indices" in exec_globals:
        indices_df = exec_globals["get_indices"](["sh", "sz", "cy"])
        market_data["indices"] = indices_df.to_dict(orient="records") if isinstance(indices_df, pd.DataFrame) else indices_df
    # 示例：假设市场宽度函数名为 get_market_breadth
    if "get_market_breadth" in exec_globals:
        breadth = exec_globals["get_market_breadth"]()
        market_data["breadth"] = breadth
except Exception as e:
    market_data["error"] = str(e)

# 3. 保存结果
output_path = os.path.join(os.path.dirname(__file__), "market_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(market_data, f, ensure_ascii=False, indent=2)
print(f"Saved market data to {output_path}")
