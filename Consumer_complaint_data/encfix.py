# fix_csv.py
import pandas as pd, pathlib, cchardet

def fix_csv(path):
    p = pathlib.Path(path)
    # 1. 编码 → UTF-8
    enc = cchardet.detect(p.read_bytes())['encoding'] or 'latin-1'
    txt = p.read_text(encoding=enc, errors='replace').rstrip() + '\n'
    p.write_text(txt, encoding='utf-8')
    # 2. 读入
    return pd.read_csv(p, engine='python', on_bad_lines='warn')

df = fix_csv('/Volumes/T9/finlit/classify.csv')
# df = df.drop(columns=['prediction'])
print(df.shape)
print(df.sample(5, random_state=42).to_string())
# 2. 专门把之前报错的尾部列印出来
print(df[-3:].to_string())
# 3. 统计缺失值/� 字符
print(df.isna().sum())
print(df.select_dtypes('object').apply(lambda s: s.str.contains('�', na=False).sum()))