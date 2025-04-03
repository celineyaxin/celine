import pandas as pd
import re

csv_file = '/Users/chenyaxin/Desktop/催收/classify_result.csv'
# 加载CSV文件
df = pd.read_csv(csv_file)
def split_model_output(output):
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

# 应用拆分函数
df['是否与催收相关'], df['模型输出_理由'] = zip(*df['模型输出'].apply(split_model_output))

df.to_csv(csv_file, index=False, encoding='utf-8-sig')

print("处理完成，结果已保存到文件中。")