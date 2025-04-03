
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re

client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = '/Users/chenyaxin/Desktop/催收/classify_result.csv'
output_file = '/Users/chenyaxin/Desktop/催收/classify_result_double.csv'
df = pd.read_csv(csv_file)

def classify_complaint(content):
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",  # 替换为你的模型名称
            messages=[
                {"role": "user", "content": f"判断以下投诉内容是否属于放贷机构进行催收相关的投诉，请回答是或否，并给出判断的理由：{content}"}
            ],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"Error classifying content: {content}. Error: {e}")
        return "分类失败"
    
def split_model_output(output):
    if not isinstance(output, str):
        output = str(output)
    output = output.strip()
    decision_match = re.match(r'^(是|否)', output)
    if decision_match:
        decision = decision_match.group(1).strip()
        reason = output[len(decision):].strip()
    else:
        # 如果没有匹配到“是”或“否”，返回空字符串
        decision = ''
        reason = output.strip()

    reason = re.sub(r'^[，。：；、\s]+', '', reason)
    reason = re.sub(r'^[^：]+：', '', reason)
    return decision, reason
   
for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
    content = row["投诉内容"]
    result = classify_complaint(content)
    df.at[index, "模型输出_R1"] = result
df['是否与催收相关_R1'], df['判断理由_R1'] = zip(*df['模型输出_R1'].apply(split_model_output))
df['一致性判断'] = (df['是否与催收相关_R1'] == df['是否与催收相关']).astype(int)
df.to_csv(output_file, index=False, header=True)
print(f"结果已写入 {output_file}")


# test能否运行
# test_rows = 1  # 测试前 5 行数据
# test_df = df.head(test_rows)  # 获取前5行数据      
# for index, row in test_df.iterrows():
#     content = row["投诉内容"]
#     result = classify_complaint(content)
#     print(f"第 {index + 1} 行：")
#     print(f"投诉内容：{content}")
#     print(f"模型输出：{result}")
#     print("-" * 50)

# test能否写入
for index, row in tqdm(df.head(5).iterrows(), total=5, desc="Processing"):
    content = row["投诉内容"]
    result = classify_complaint(content)
    df.at[index, "模型输出_R1"] = result
df['是否与催收相关_R1'], df['判断理由_R1'] = zip(*df['模型输出_R1'].apply(split_model_output))
df['一致性判断'] = (df['是否与催收相关_R1'] == df['是否与催收相关']).astype(int)
df.head(5).to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"处理完成前5条结果已保存到 {output_file}")

