
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re


client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud.csv'
output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud_v2.5.csv'
df = pd.read_csv(csv_file)

def classify_informed_consent_violation(content):
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",  
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是金融消费者保护领域的专家，请根据下方标准判断用户投诉中的欺诈行为是否**侵犯了消费者对个人信息的知情权**。\n\n"
                        "【侵犯知情权标准】：\n"
                        "1. 未明确告知收集/使用个人信息的目的、方式和范围\n"
                        "2. 未获得消费者明确同意而收集/使用信息\n"
                        "3. 未提供查询/更正/删除个人信息的途径\n"
                        "4. 未说明信息存储和保护措施\n"
                        "5. 其他违反知情权原则的情形\n\n"
                        "仅当投诉内容中明确存在上述情形时，才判断为'是'。\n\n"
                        "请仔细阅读投诉内容，并回答：\n"
                        "如果确认侵犯知情权，请输出：“是：”后加上具体违反情形\n"
                        "如果未提及或不符合标准，请输出：“否：”后加上简要原因\n\n"
                        "输出示例：\n"
                        "“是：未告知收集身份证照片的真实用途”\n"
                        "“否：投诉未涉及信息收集环节”"
                    )
                },
                {
                    "role": "user",
                    "content": f"投诉内容：{content}"
                }
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"异常：{e}"
def split_model_output(output):
    if not isinstance(output, str):
        output = str(output)
    output = output.strip()

    # 正则提取开头是“是”或“否”的判断
    match = re.match(r'^(是|否)[：:，、\s]*(.*)$', output)
    if match:
        decision = match.group(1)
        reason = match.group(2).strip()
    else:
        # 无法识别决策，只当作原因处理
        decision = ''
        reason = output

    return decision, reason

def save_df(df, output_file, index=False, mode='a', header=False):
    df.to_csv(output_file, index=index, header=header, mode=mode)

chunk_size = 50  # 每50条写入一次

try:
    # 判断是否已有文件决定是否写入表头
    try:
        pd.read_csv(output_file, nrows=0)
        header = False
    except FileNotFoundError:
        header = True

    for start in tqdm(range(0, len(df), chunk_size), desc="Processing"):
        end = start + chunk_size
        chunk = df.iloc[start:end].copy()
        for idx in range(start, min(end, len(df))):
            content = df.at[idx, "投诉内容"]
            output = classify_informed_consent_violation(content)
            decision, reason = split_model_output(output)

            df.at[idx, "模型输出"] = output
            df.at[idx, "是否侵犯了个人信息的知情权"] = decision
            df.at[idx, "模型判定理由"] = reason

        # 写入结果
        if start == 0 and header:
            save_df(df.iloc[start:end], output_file, index=False, mode='w', header=True)
        else:
            save_df(df.iloc[start:end], output_file, index=False, mode='a', header=False)
        print(f"结果已写入 {output_file}")

except Exception as e:
    print(f"处理过程中发生异常: {e}")
    save_df(df, output_file, index=False, mode='w', header=True)
    print(f"异常中断时的结果已保存到临时文件 {output_file}")

     
# test运行情况
# chunk_size = 5  # 每5条处理一次

# for start in tqdm(range(0, min(len(df), chunk_size)), desc="Processing"):
#     content = df.at[start, "投诉内容"]
#     output = classify_privacy_independence_with_reason(content)
#     decision, reason = split_model_output(output)

#     df.at[start, "模型输出"] = output
#     df.at[start, "是否完全不依赖隐私"] = decision
#     df.at[start, "判定理由"] = reason
    
# # 打印结果
# print("处理结果：")
# print(df[["投诉内容", "是否完全不依赖隐私", "判定理由"]].head(chunk_size))





