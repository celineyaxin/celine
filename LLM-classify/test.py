
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 

client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = "/Users/chenyaxin/Desktop/上市公司投诉数据探究/data/绿色新闻/随机抽取的数据.csv"  # 替换为你的 CSV 文件路径
df = pd.read_csv(csv_file)

green_news_df = df[df["是否绿色相关"] == "是"]

def classify_sentiment(content):
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V2.5",  # 替换为你的模型名称
            messages=[
                {"role": "user", "content": f"判断以下绿色新闻内容的情感倾向（正面、负面或中性）：{content}"}
            ]
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"Error classifying content: {content}. Error: {e}")
        return "分类失败"

tqdm.pandas(desc="情感分类进度") 
green_news_df["情感分类结果"] = green_news_df["正文"].progress_apply(classify_sentiment)
df.loc[green_news_df.index, "情感分类结果"] = green_news_df["情感分类结果"]

# 保存到原 CSV 文件
df.to_csv(csv_file, index=False)

print(f"情感分类完成，结果已保存到原文件 {csv_file}")


# test_rows = 5
# print(f"开始测试前 {test_rows} 行绿色新闻的情感分类结果：")
# for index, row in green_news_df.head(test_rows).iterrows():
#     content = row["正文"]
#     result = classify_sentiment(content)
#     print(f"第 {index + 1} 行：")
#     print(f"新闻内容：{content}")
#     print(f"情感分类结果：{result}")
#     print("-" * 50)



