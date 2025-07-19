
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re
import json

client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud.csv'
output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud_v2.5.csv'
df = pd.read_csv(csv_file)

# 强制购买（塔售）/强制下款/自动划扣/精准推荐
# 诱导消费/虚假服务/冒充平台
## 根据欺诈类型分类
def classify_complaint_with_reason(content):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是金融消费者保护领域的专家。请仔细阅读投诉内容，判断涉及哪些违法行为（可多选）。"
                        "然后请为每个判定的违法行为写出你自己的判定理由，简要说明为什么你认为投诉属于该类别。\n\n"
                        "请以JSON格式返回，结构如下：\n"
                        "{\n"
                        "  \"labels\": [\"1.1\", \"3.2\"],\n"
                        "  \"reasons\": {\n"
                        "    \"1.1\": \"这是模型基于投诉内容自己写的判定理由\",\n"
                        "    \"3.2\": \"这是模型基于投诉内容自己写的判定理由\"\n"
                        "  }\n"
                        "}\n"
                        "不要输出除JSON以外的其他内容。\n\n"
                        "子类目：\n"
                        "1.1 强制放贷 / 自动下款\n"
                        "1.2 高利贷 / 超额年化利率\n"
                        "1.3 虚假到账 / 砍头息\n"
                        "1.4 拒绝提前还款 / 利率误导\n"
                        "2.1 虚假宣传 / 诱导贷款\n"
                        "2.2 虚假合同 / 阴阳条款\n"
                        "2.3 虚构会员服务 / 诱导付费\n"
                        "2.4 商品捆绑销售 / 虚假权益礼包\n"
                        "3.1 隐性费用 / 服务费不透明\n"
                        "3.2 非法收费 / 保险、评估、检测费\n"
                        "3.3 自动扣款 / 未授权付款\n"
                        "4.1 非授权操作（如盗刷、账户关联）\n"
                        "4.2 信息滥用 / 擅自共享或非法披露\n"
                        "4.3 引导授权欺诈（默认勾选、暗示支付）"
                    )
                },
                {
                    "role": "user",
                    "content": f"投诉内容：{content}"
                }
            ],
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        parsed = json.loads(result)
        if "labels" in parsed and "reasons" in parsed:
            return parsed
        else:
            return {"error": "格式错误，未包含labels或reasons字段"}
    except Exception as e:
        print(f"Error classifying content: {content}. Error: {e}")
        return {"error": "分类失败"}
   

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

chunk_size = 50  # 每50条保存一次

def save_df(df, output_file, index=False, mode='a', header=False):
    df.to_csv(output_file, index=index, header=header, mode=mode)

try:
    try:
        pd.read_csv(output_file, nrows=0)
        header = False
    except FileNotFoundError:
        header = True

    for start in tqdm(range(0, len(df), chunk_size), desc="Processing"):
        end = start + chunk_size
        chunk = df.iloc[start:end].copy()
        for index in range(start, min(end, len(df))):
            content = df.at[index, "投诉内容"]
            result = classify_complaint_with_reason(content)
            df.at[index, "模型输出"] = json.dumps(result)
            if "labels" in result and "reasons" in result:
                df.at[index, "标签"] = ", ".join(result["labels"])
                df.at[index, "判定理由"] = json.dumps(result["reasons"], ensure_ascii=False)
            else:
                df.at[index, "标签"] = "分类失败"
                df.at[index, "判定理由"] = result.get("error", "未知错误")
        if start == 0:
            save_df(df.iloc[start:end], output_file, index=False, mode='w', header=True)  # 第一次写入时添加表头
        else:
            save_df(df.iloc[start:end], output_file, index=False, mode='a', header=False)  # 后续追加时不添加表头
        print(f"结果已写入 {output_file}")
            
except Exception as e:
    print(f"处理过程中发生异常: {e}")
    save_df(df, output_file, index=False, mode='w', header=True)
    print(f"异常中断时的结果已保存到临时文件 {output_file}")
     

# test运行情况
# chunk_size = 5  # 每5条处理一次

# for start in tqdm(range(0, min(len(df), chunk_size)), desc="Processing"):
#     content = df.at[start, "投诉内容"]
#     result = classify_complaint_with_reason(content)
#     df.at[start, "模型输出"] = json.dumps(result)
#     if "labels" in result and "reasons" in result:
#         df.at[start, "标签"] = ", ".join(result["labels"])
#         df.at[start, "判定理由"] = json.dumps(result["reasons"], ensure_ascii=False)
#     else:
#         df.at[start, "标签"] = "分类失败"
#         df.at[start, "判定理由"] = result.get("error", "未知错误")

# # 打印结果
# print("处理结果：")
# print(df[["投诉内容", "模型输出", "标签", "判定理由"]].head(chunk_size))





