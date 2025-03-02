import pandas as pd

# 读取 CSV 文件
csv_file = "/Users/chenyaxin/Desktop/classified_file.csv"  # 替换为你的 CSV 文件路径
df = pd.read_csv(csv_file)

def parse_model_output(output):
    # 先检查是否明确不属于退改相关投诉
    if "不属于退改相关的投诉" in output or "与机票的退改政策无直接关联" in output or "不属于典型的退改相关投诉" in output:
        return "否"
    # 再检查是否明确属于退改相关投诉
    elif "属于退改相关的投诉" in output or "退改相关的投诉" in output:
        return "是"
    # 如果没有明确的判断，则标记为未知
    else:
        return "未知"

df["是否属于退改相关内容"] = df["模型输出结果"].apply(parse_model_output)

# 保存到原始 CSV 文件
df.to_csv(csv_file, index=False)

print(f"解析完成，结果已更新到原始文件 {csv_file}")
