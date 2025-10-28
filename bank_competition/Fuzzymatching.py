# -*- coding: utf-8 -*-
import pandas as pd
from rapidfuzz import fuzz

# 1. 读文件（列名已对齐）
unmatched_file = "/Users/chenyaxin/Desktop/未匹配的持牌金融机构.xlsx"
freq_file = "/Users/chenyaxin/Desktop/信息规范/行政处罚需要完整的全称/机构名称频率统计_增强版的副本.xlsx"

df_unmatch = pd.read_excel(unmatched_file, usecols=[0], names=["机构名称"]).dropna()
df_freq    = pd.read_excel(freq_file,usecols=[0], names=["模型生成全称"]).dropna()

short_list = df_unmatch["机构名称"].astype(str).tolist()
long_list  = df_freq["模型生成全称"].astype(str).tolist()

# 2. 参数
THRESHOLD = 75   # 可调

# 3. 匹配
res = []
for short in short_list:
    score, long = fuzz.WRatio(short, long_list), None
    if score >= THRESHOLD:
        long = max(long_list, key=lambda x: fuzz.WRatio(short, x))   # 取最高
        res.append({"简称": short, "最相似全称": long, "相似度": round(score, 2)})

# 4. 输出
out_df = pd.DataFrame(res)
out_file = "/Users/chenyaxin/Desktop/未匹配_相似度复核.xlsx"
out_df.to_excel(out_file, index=False)
print(f"完成！{len(res)} 条≥{THRESHOLD} -> {out_file}")