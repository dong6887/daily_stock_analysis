import os, json, re, requests, pandas as pd

# 1. 联网拉取 SKILL.md
url = "https://raw.githubusercontent.com/simonlin1212/a-stock-data/main/SKILL.md"
response = requests.get(url)
response.raise_for_status()
skill_content = response.text

# 2. 提取所有 python 代码块
code_blocks = re.findall(r"```python\n(.*?)```", skill_content, re.DOTALL)

# 3. 过滤执行
exec_globals = {}
for code in code_blocks:
    safe_lines = []
    for line in code.split('\n'):
        if line.strip().startswith("norm_ticker(") or line.strip().startswith("print("):
            continue
        safe_lines.append(line)
    try:
        exec('\n'.join(safe_lines), exec_globals)
    except Exception:
        pass

market_data = {}

# ==================== 抓取指数 ====================
try:
    index_funcs = [k for k in exec_globals.keys() if "index" in k.lower() and callable(exec_globals[k])]
    if index_funcs:
        print(f"找到指数函数: {index_funcs[0]}")
        indices_df = exec_globals[index_funcs[0]](["sh", "sz", "cy"])
        market_data["indices"] = indices_df.to_dict(orient="records") if isinstance(indices_df, pd.DataFrame) else indices_df
except Exception as e:
    market_data["index_error"] = str(e)

# ==================== 抓取涨跌家数（重点硬刚） ====================
try:
    # 自动搜索名字里带有 breadth(宽度), advance(上涨), up_down(涨跌) 的函数
    breadth_funcs = [k for k in exec_globals.keys() if any(word in k.lower() for word in ["breadth", "advance", "up_down", "updown"]) and callable(exec_globals[k])]
    print(f"找到涨跌家数相关函数: {breadth_funcs}")
    
    if breadth_funcs:
        target_breadth_func = breadth_funcs[0]
        print(f"正在尝试调用涨跌家数函数: {target_breadth_func}")
        # 尝试调用
        breadth_data = exec_globals[target_breadth_func]()
        market_data["breadth"] = breadth_data.to_dict(orient="records") if isinstance(breadth_data, pd.DataFrame) else breadth_data
    else:
        # 如果没找到特定的名字，把所有可用的函数名打出来，方便我们下一步排查
        all_public_funcs = [k for k in exec_globals.keys() if not k.startswith("__") and callable(exec_globals[k])]
        print(f"未能精确匹配，当前库中所有可用函数有: {all_public_funcs}")
except Exception as e:
    market_data["breadth_error"] = str(e)
    print(f"抓取涨跌家数报错: {e}")

# ==================== 保存结果 ====================
output_path = os.path.join(os.path.dirname(__file__), "market_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(market_data, f, ensure_ascii=False, indent=2)
print(f"Saved market data to {output_path}")
