from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re
import os
import time

client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud.csv'
output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/sample_fraud_弱势群体.csv'
df = pd.read_csv(csv_file)

# 优化后的分类函数
def classify_financial_vulnerability(content):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一名金融消费者保护专家，请根据以下特征识别投诉人是否属于金融素养弱势群体：\n\n"
                        "【金融素养弱势群体特征】\n"
                        "1. 对金融产品/服务的基本概念缺乏理解（如利息计算、风险等级）\n"
                        "2. 被复杂合同条款或专业术语困惑\n"
                        "3. 明显受到销售人员诱导性话术影响\n"
                        "4. 表现出对金融风险认知不足（如未意识投资风险）\n"
                        "5. 属于易受骗人群（老年人、低学历者、经济困难者等）\n\n"
                        "【判断标准】\n"
                        "若投诉内容中明确显示至少1项上述特征，则回答：“是：”+简要原因\n"
                        "若无明确证据显示上述特征，则回答：“否：”+简要原因\n\n"
                        "请专注于文本内容本身，避免主观臆断。输出格式示例：\n"
                        "“是：投诉人明显不理解分期付款的利息计算方式”\n"
                        "“否：投诉主要涉及服务延迟，未体现金融知识缺乏”"
                    )
                },
                {
                    "role": "user",
                    "content": f"投诉内容：{content}"
                }
            ],
            temperature=0.2,  # 稍高的温度值允许一定创造性
            max_tokens=150
        )
        output = response.choices[0].message.content.strip()
        return output
    except Exception as e:
        print(f"API调用异常: {e}")
        time.sleep(10)  # 遇到错误时暂停
        return f"异常：{str(e)[:50]}"  # 截断异常信息

def split_model_output(output):
    if not isinstance(output, str):
        output = str(output)
    
    # 增强的匹配模式
    match = re.match(r'^(是|否)[：:]\s*(.+)$', output)
    if match:
        return match.group(1), match.group(2)
    
    # 处理特殊响应格式
    if "是" in output[:10]:
        return "是", output[output.index("是")+1:].strip()
    elif "否" in output[:10]:
        return "否", output[output.index("否")+1:].strip()
    
    return "未知", output  # 无法解析时保留原始输出

# 文件保存函数（优化后）
def save_data(df_chunk, output_file, is_first_chunk):
    mode = 'w' if is_first_chunk else 'a'
    header = is_first_chunk
    df_chunk.to_csv(output_file, index=False, mode=mode, header=header, encoding='utf-8-sig')

# 主处理流程
try:
    # 初始化新列
    df["模型输出"] = ""
    df["是否弱势群体"] = ""
    df["判定理由"] = ""
    
    # 断点续处理
    start_index = 0
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        start_index = len(existing_df)
        print(f"检测到已有{start_index}条记录，将继续处理...")
    
    chunk_size = 30  # 减小批次大小提高稳定性
    total = len(df)
    
    for start in tqdm(range(start_index, total, chunk_size), desc="处理进度"):
        end = min(start + chunk_size, total)
        for idx in range(start, end):
            content = df.at[idx, "投诉内容"]
            output = classify_financial_vulnerability(content)
            decision, reason = split_model_output(output)
            
            df.at[idx, "模型输出"] = output
            df.at[idx, "是否弱势群体"] = decision
            df.at[idx, "判定理由"] = reason
        
        # 保存当前批次
        save_data(df.iloc[start:end], output_file, start == 0)
        print(f"\n已保存 {end}/{total} 条记录")
        
        time.sleep(1)  # 批次间暂停避免速率限制

except Exception as e:
    print(f"\n处理中断于 {start} 条: {str(e)}")
    # 尝试保存已处理部分
    if 'start' in locals():
        save_data(df.iloc[:start], output_file + ".backup", True)
        print(f"已备份处理结果至 {output_file}.backup")