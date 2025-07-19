
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re
import json

client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud.csv'
output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud_v2.5.csv'
df = pd.read_csv(csv_file)

# 根据业务类型分类
def classify_complaint_with_reason(content):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个严格的金融业务分类专家。请分析投诉内容，判断涉及哪些业务类型（可多选）。"
                        "业务类型定义："
                        "- 网贷/现金贷业务：涉及网络贷款、现金借贷等业务"
                        "- 信用卡业务：涉及银行信用卡相关业务"
                        "- 消费分期业务：涉及商品或服务消费的分期付款业务"
                        "- 支付/扣费业务：涉及支付交易、资金扣款等业务"
                        "请严格只输出JSON格式，不要包含任何其他文本。"
                        "输出结构："
                        '{"labels":["业务类型1","业务类型2"],"reasons":{"业务类型1":"理由1","业务类型2":"理由2"}}'
                    )
                },
                {
                    "role": "user",
                    "content": f"投诉内容：{content}"
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = response.choices[0].message.content.strip()
        
        # 尝试提取有效的JSON部分
        json_start = result.find('{')
        json_end = result.rfind('}') + 1
        
        if json_start != -1 and json_end != 0:
            json_str = result[json_start:json_end]
            try:
                parsed = json.loads(json_str)
                if "labels" in parsed and "reasons" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass  # 继续尝试其他方法
        
        # 如果上述方法失败，尝试直接解析
        try:
            parsed = json.loads(result)
            if "labels" in parsed and "reasons" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass
        
        # 如果所有方法都失败，返回错误信息
        return {"error": f"JSON解析失败: {result[:100]}..."}
    
    except Exception as e:
        return {"error": f"API调用失败: {str(e)}"}

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





