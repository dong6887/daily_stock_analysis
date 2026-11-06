import os, json, re, requests, pandas as pd

# 1. 联网拉取 SKILL.md
url = "https://raw.githubusercontent.com/simonlin1212/a-stock-data/main/SKILL.md"
response = requests.get(url)
response.raise_for_status()
skill_content = response.text

# 2. 提取所有 python 代码块并执行
code_blocks = re.findall(r"```python\n(.*?)```", skill_content, re.DOTALL)
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
        indices_df = exec_globals[index_funcs[0]](["sh", "sz", "cy"])
        market_data["indices"] = indices_df.to_dict(orient="records") if isinstance(indices_df, pd.DataFrame) else indices_df
except Exception as e:
    market_data["index_error"] = str(e)

# ==================== 抓取涨跌家数（硬编码东方财富API） ====================
try:
    print("正在直接请求东方财富获取全市场涨跌家数...")
    # 东方财富全市场行情API，f104=上涨家数, f105=下跌家数, f106=平盘家数
    em_url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=1&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23&fields=f104,f105,f106"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(em_url, headers=headers, timeout=10).json()
    
    if resp and resp.get("data"):
        market_data["breadth"] = {
            "up_count": resp["data"]["f104"],
            "down_count": resp["data"]["f105"],
            "flat_count": resp["data"]["f106"]
        }
        print(f"成功获取涨跌家数: {market_data['breadth']}")
except Exception as e:
    market_data["breadth_error"] = str(e)
    print(f"获取涨跌家数失败: {e}")

# ==================== 保存结果 ====================
output_path = os.path.join(os.path.dirname(__file__), "market_data.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(market_data, f, ensure_ascii=False, indent=2)
print(f"Saved market data to {output_path}")
