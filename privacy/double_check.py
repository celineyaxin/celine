
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re


client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud_qw3-8B.csv'
output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud_qw3-32B.csv'
df = pd.read_csv(csv_file)

def classify_privacy_independence_with_reason(content):
    try:
        response = client.chat.completions.create(
            model="THUDM/GLM-Z1-9B-0414",  # Qwen/Qwen3-32B
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是金融消费者保护领域的专家，请根据下方标准判断用户投诉中的欺诈行为是否**完全不依赖**个人信息：\n\n"
                        "【完全不依赖个人信息】：\n"
                        "指投诉中所描述的欺诈行为，从开始到结束均不需要获取、滥用或使用用户的个人信息（包括身份信息、账户信息、联系人、银行卡号、手机号等），"
                        "即使商家或平台根本不知道用户是谁，也依然可以完成该欺诈。\n\n"
                        "请仔细阅读投诉文本，如果你确定其属于‘完全不依赖个人信息’，请回答：“是：”后加上简要原因。\n"
                        "如果你不确定或认为它依赖个人信息，请回答：“否：”后加上简要原因。\n\n"
                        "只输出判断 + 原因，例如：“否：平台通过收集手机号和联系人实施精准欺诈”。"
                    )
                },
                {
                    "role": "user",
                    "content": f"投诉内容：{content}"
                }
            ],
            temperature=0
        )
        output = response.choices[0].message.content.strip()
        return output
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
            output = classify_privacy_independence_with_reason(content)
            decision, reason = split_model_output(output)

            df.at[idx, "模型输出_qw"] = output
            df.at[idx, "是否完全依赖个人信息_qw"] = decision
            df.at[idx, "模型判定理由_qw"] = reason
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
           
    df['一致性判断'] = (df['是否完全依赖个人信息'] == df['是否完全依赖个人信息_qw']).astype(int)
    save_df(df, output_file, index=False, mode='w', header=True)

except Exception as e:
    print(f"处理过程中发生异常: {e}")
    save_df(df, output_file, index=False) 
