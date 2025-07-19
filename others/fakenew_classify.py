from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re
import random
import os

# 初始化OpenAI客户端
client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", 
                base_url="https://api.siliconflow.cn/v1")

# 文件路径
excel_file = '/Users/chenyaxin/Desktop/最终谣言数据.xlsx'
# output_file = '/Users/chenyaxin/Desktop/sample_fake.csv'
output_file = '/Users/chenyaxin/Desktop/sample_fake_R1.csv'

# 1. 从Excel中随机抽取1000条数据
df = pd.read_excel(excel_file)
df.dropna(how='all', inplace=True)
df = df.dropna(subset=['提问内容'])
df = df[df['提问内容'].str.strip().astype(bool)]
if len(df) > 1000:
    df = df.sample(n=1000, random_state=42)  # 随机抽样1000条

# 只保留需要的列
df = df[['序号', '提问内容']].copy()
df.reset_index(drop=True, inplace=True)  # 重置索引为连续整数

df['虚假消息判断'] = ""
df['判断理由'] = ""

# 检查文件是否存在，不存在则创建
if not os.path.exists(output_file):
    df.head(0).to_csv(output_file, index=False)
    print(f"创建新文件并写入表头: {output_file}")
else:
    print(f"文件已存在，将追加结果: {output_file}")


def classify_fake_news(content):
    """判断内容是否为虚假消息"""
    try:
        response = client.chat.completions.create(
            # model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",  # deepseek-ai/DeepSeek-R1
            model="deepseek-ai/DeepSeek-R1",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是专业的谣言检测助手。请判断用户提供的内容是否属于虚假消息（谣言）。\n\n"
                        "如果是虚假消息，请回答：\"是：\" + 简要理由\n"
                        "如果不是虚假消息，请回答：\"否：\" + 简要理由\n"
                        "理由要简洁明了，不要复杂。"
                    )
                },
                {
                    "role": "user",
                    "content": f"内容：{content}"
                }
            ],
            temperature=0,
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"API调用异常: {e}")
        return f"异常：{e}"
    
def split_model_output(output):
    """分割模型输出为判断和理由 - 更灵活的版本"""
    output = str(output).strip()
    
    # 更灵活的正则匹配：允许任意长度理由，支持多种分隔符
    match = re.match(r'^(是|否)[：:，、\s]\s*(.*?)$', output)
    if match:
        decision = match.group(1)
        reason = match.group(2).strip()
        # 自动截断过长的理由
        if len(reason) > 30:
            reason = reason[:27] + "..."
        return decision, reason
    else:
        return "未知", output[:30] if len(output) > 30 else output

try:
    processed_count = 0  # 已处理计数器
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="处理进度"):
        if not pd.isna(df.at[idx, '虚假消息判断']) and df.at[idx, '虚假消息判断'] != '':
            continue  # 如果已处理过，跳过
      
        content = row['提问内容']
        if pd.isna(content) or not content.strip():
            df.at[idx, '虚假消息判断'] = "否"
            df.at[idx, '判断理由'] = "内容为空"
        else:
            result = classify_fake_news(content[:2000])
            decision, reason = split_model_output(result)
            df.at[idx, '虚假消息判断'] = decision
            df.at[idx, '判断理由'] = reason
        current_row = df.iloc[[idx]]
        current_row.to_csv(output_file, mode='a', header=False, index=False)
        processed_count += 1
        if processed_count % 50 == 0:
            print(f"已处理 {processed_count}/{len(df)} 条数据")
    print(f"处理完成！共处理 {processed_count} 条数据，结果已保存至: {output_file}")

except Exception as e:
    print(f"处理中断: {e}")
    print(f"已保存的进度: {processed_count} 条数据")



