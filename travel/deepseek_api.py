
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 

client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = "/Users/chenyaxin/Desktop/互联网旅游公约/treatment_sample.csv"  # 替换为你的 CSV 文件路径
df = pd.read_csv(csv_file)

def classify_complaint(content):
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V2.5",  # 替换为你的模型名称
            messages=[
                {"role": "user", "content": f"判断以下内容是否与退改相关的投诉，并给出理由：{content}"}
            ]
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"Error classifying content: {content}. Error: {e}")
        return "分类失败"

tqdm.pandas(desc="分类进度") 
df["模型输出结果"] = df["发起投诉内容"].progress_apply(classify_complaint)

df.to_csv(csv_file, index=False)

print(f"分类完成，结果已保存到 {csv_file}")

# test_rows = 5  # 测试前 5 行数据
# for index, row in df.head(test_rows).iterrows():
#     content = row["正文"]
#     result = classify_complaint(content)
#     print(f"第 {index + 1} 行：")
#     print(f"投诉内容：{content}")
#     print(f"模型输出：{result}")
#     print("-" * 50)



