import pandas as pd
import re

csv_file = "/Users/chenyaxin/Desktop/上市公司投诉数据探究/data/绿色新闻/随机抽取的数据.csv"  # 替换为你的 CSV 文件路径
df = pd.read_csv(csv_file)

# 定义一个函数，根据模型输出内容的特征判断是否为绿色相关新闻
def is_green_related(model_output):
    # 定义负面关键词列表
    negative_keywords = ["不是", "不直接涉及", "无关", "不属于", "没有直接关联", "并非", "不涉及", "相关性不大", "相关的程度较低", "没有直接关系",
                         "相关的可能性较低", "非直接相关"]
    # 定义正面关键词列表（用于进一步确认）
    positive_keywords = ["是", "相关", "是的", "有关"]
    
    # 提取模型输出中的判断部分（假设判断部分在理由之前）
    # 使用正则表达式匹配判断部分
    match = re.match(r"^(.*?)(理由如下：|理由：)", model_output, re.DOTALL)
    if match:
        judgment_part = match.group(1).strip()
    else:
        judgment_part = model_output

    for keyword in negative_keywords:
        if keyword in judgment_part:
            return "否"
    
    # 如果判断部分不包含负面关键词，检查是否包含正面关键词
    for keyword in positive_keywords:
        if keyword in judgment_part:
            return "是"
    
    # 如果既没有负面关键词也没有正面关键词，判断为“否”
    return "未完全识别"

df["是否绿色相关"] = df["模型输出结果"].apply(is_green_related)

# 将结果保存到新的CSV文件中
df.to_csv(csv_file, index=False)

print("处理完成，结果已保存到文件中。")