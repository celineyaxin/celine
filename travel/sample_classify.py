import pandas as pd
import openai
import json
import time
from tqdm import tqdm
from openai import OpenAI

# 设置OpenAI客户端 - 使用硅基流动的API
client = OpenAI(
    api_key="sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol",  # 请替换为您的实际API密钥
    base_url="https://api.siliconflow.cn/v1"
)

# 读取CSV文件
input_file = '/Users/chenyaxin/Desktop/InternetTourismConvention/travel_sample.csv'  # 输入文件名
output_csv_file = '/Users/chenyaxin/Desktop/travel_sample_qw.csv'  # 输出文件名
output_excel_file = '/Users/chenyaxin/Desktop/travel_sample_qw.xlsx'  # 输出文件名

df = pd.read_csv(input_file)

# 定义提示模板 - 扩展了退改相关场景的描述
def create_prompt(content):
    prompt = f"""
请判断以下投诉内容是否与退改相关（包括但不限于：退款、改签、更改行程、取消订单、退票、退房、改期等，涉及旅游、酒店、门票、航班、预订服务等场景）。
请只输出一个JSON对象，包含两个字段：is_related（布尔值）和reason（字符串）。

投诉内容：{content}
"""
    return prompt

# 调用模型函数 - 使用硅基流动的API格式
def ask_model(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="Qwen/QwQ-32B",  # 使用您指定的模型
                messages=[
                    {"role": "system", "content": "您是一个专业的客服助手，用于判断投诉内容是否与退改相关。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0,
                stream=False  # 不使用流式传输，以便一次性获取完整响应
            )
            
            # 提取响应内容
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            return None
        except Exception as e:
            print(f"API调用出错 (尝试 {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

# 初始化结果列（如果不存在）
if '是否退改相关' not in df.columns:
    df['是否退改相关'] = None
if '理由' not in df.columns:
    df['理由'] = None

# 分块处理数据
chunk_size = 50  # 每50条写入一次
total_rows = len(df)

# 创建进度条
with tqdm(total=total_rows, desc="处理进度") as pbar:
    for start_idx in range(0, total_rows, chunk_size):
        end_idx = min(start_idx + chunk_size, total_rows)
        
        # 处理当前块
        for idx in range(start_idx, end_idx):
            if pd.isna(df.at[idx, '是否退改相关']):  # 只处理尚未处理的行
                content = df.at[idx, '发起投诉内容']  # 假设列名为'投诉内容'
                prompt = create_prompt(content)
                response_text = ask_model(prompt)
                
                # 初始化默认值
                is_related = False
                reason = "无法判断"
                
                if response_text:
                    try:
                        # 尝试解析JSON响应
                        # 有时模型可能会在JSON前后添加额外文本，尝试提取JSON部分
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = response_text[json_start:json_end]
                            response_json = json.loads(json_str)
                            is_related = response_json.get('is_related', False)
                            reason = response_json.get('reason', '无理由提供')
                        else:
                            # 如果没有找到JSON，尝试手动解析
                            if "是" in response_text or "true" in response_text.lower():
                                is_related = True
                            reason = response_text  # Fallback: 使用整个响应作为理由
                    except json.JSONDecodeError:
                        # 如果JSON解析失败，尝试手动解析
                        if "是" in response_text or "true" in response_text.lower():
                            is_related = True
                        reason = response_text  # Fallback: 使用整个响应作为理由
                else:
                    reason = "API调用失败"
                
                df.at[idx, '是否退改相关'] = is_related
                df.at[idx, '理由'] = reason
                
                # 添加延迟以避免API速率限制
                time.sleep(1)
            
            # 更新进度条
            pbar.update(1)
            pbar.set_postfix(当前处理=f"{idx+1}/{total_rows}")
        
        # 每处理完一个块就保存一次
        df.to_csv(output_csv_file, index=False, encoding='utf-8-sig')
        print(f"\n已保存第 {start_idx//chunk_size + 1} 块数据 ({start_idx}-{end_idx-1})")

print("处理完成，正在转换为Excel格式...")
df.to_excel(output_excel_file, index=False)
print(f"结果已保存到 {output_excel_file}")

# 可选：询问是否删除CSV文件
delete_csv = input("是否删除临时的CSV文件？(y/n): ")
if delete_csv.lower() == 'y':
    import os
    os.remove(output_csv_file)
    print(f"已删除临时文件 {output_csv_file}")
else:
    print(f"CSV文件已保留: {output_csv_file}")
print("处理完成，结果已保存到", output_csv_file)