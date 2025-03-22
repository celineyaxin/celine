
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 

client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/上市公司信息筛选/classify_sample.csv'
df = pd.read_csv(csv_file)

def classify_complaint(content,category):
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V2.5",  # 替换为你的模型名称
            messages=[
                {"role": "user", "content": f"判断以下内容是否与{category}相关的投诉，请回答是或否，并给出判断的理由：{content}"}
            ]
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"Error classifying content: {content}. Error: {e}")
        return "分类失败"
def classify_quality(content):
    return classify_complaint(content, "产品和服务本身质量")

def classify_experience(content):
    return classify_complaint(content, "消费体验")

# tqdm.pandas(desc="分类进度") 
# df["质量相关投诉"] = df["发起投诉内容"].progress_apply(classify_quality)
# df["体验相关投诉"] = df["发起投诉内容"].progress_apply(classify_experience)
df["是否与质量相关投诉"] = df["质量相关投诉"].apply(lambda x: 1 if x.strip() == "是" else (0 if x.strip() == "否" else -1))
df["是否与体验相关投诉"] = df["体验相关投诉"].apply(lambda x: 1 if x.strip() == "是" else (0 if x.strip() == "否" else -1))
# df.to_csv(csv_file, index=False)
# print(f"分类完成，结果已保存到 {csv_file}")

test_rows = 5  # 测试前 5 行数据
test_df = df.head(test_rows)  # 获取前5行数据
test_df["质量相关投诉"] = test_df["发起投诉内容"].apply(classify_quality)
test_df["体验相关投诉"] = test_df["发起投诉内容"].apply(classify_experience)

for index, row in test_df.iterrows():
    content = row["发起投诉内容"]
    quality_result = row["质量相关投诉"]
    experience_result = row["体验相关投诉"]
    print(f"第 {index + 1} 行：")
    print(f"投诉内容：{content}")
    print(f"质量相关投诉模型输出：{quality_result}")
    print(f"体验相关投诉模型输出：{experience_result}")
    print("-" * 50)



