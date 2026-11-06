import os, json, re, requests, pandas as pd

# 1. 联网拉取 SKILL.md
url = "https://raw.githubusercontent.com/simonlin1212/a-stock-data/main/SKILL.md"
response = requests.get(url)
response.raise_for_status()
skill_content = response.text

# 2. 提取所有 python 代码块
code_blocks = re.findall(r"```python\n(.*?)```", skill_content, re.DOTALL)

# 3. 过滤掉会引发崩溃的“测试代码”和“执行代码”
# 我们只保留函数定义和类的定义
exec_globals = {}
for code in code_blocks:
    safe_lines = []
    for line in code.split('\n'):
        # 如果这行代码以 `norm_ticker(` 开头，或者包含测试语句，跳过
        if line.strip().startswith("norm_ticker(") or line.strip().startswith("print("):
            continue
        safe_lines.append(line)
    
    safe_code = '\n'.join(safe_lines)
    try:
        # 用 try 包起来，就算某个代码块有语法错，也不影响整体
        exec(safe_code, exec_globals)
    except Exception as e:
        print(f"跳过出错的代码块: {e}")

# 4. 尝试调用函数
market_data = {}
try:
    # 根据之前它内置的报错，可能叫 get_indices 或者 get_index_data
    # 我们顺便把里面所有带 index 的函数名找出来
    index_funcs = [k for k in exec_globals.keys() if "index" in k.lower() and callable(exec_globals[k])]
    print(f"找到的指数相关函数有: {index_funcs}")
    
    if index_funcs:
        # 尝试调用第一个找到的函数
        target_func = index_funcs[0]
        print(f"正在尝试调用: {target_func}")
        # 传递深证和创业板代码
        indices_df = exec_globals[target_func](["sz", "cy"]) 
        market_data["indices"] = indices_df.to_dict(orient="records") if isinstance(indices_df, pd.DataFrame) else indices_df
except Exception as e:
    market_data["error"] = str(e)

# 5. 保存结果
output_path = os.path.join(os.path.dirname(__file__), "market_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(market_data, f, ensure_ascii=False, indent=2)
print(f"Saved market data to {output_path}")
