import pandas as pd
import random
import os
import time
import json
from openai import OpenAI
import uuid

# 初始化API客户端
client = OpenAI(
    api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", 
    base_url="https://api.siliconflow.cn/v1"
)

# 生成唯一任务ID，避免多任务冲突
TASK_ID = str(uuid.uuid4())[:8]  # 生成8位唯一ID
print(f"当前任务ID: {TASK_ID}")

def filter_2019_complaints(input_file):
    """筛选2019年投诉数据"""
    try:
        # 读取CSV文件
        df = pd.read_csv(input_file)
        print(f"数据总条数: {len(df)}")
        print(f"列名: {df.columns.tolist()}")
        
        # 自动检测日期列名
        date_columns = [col for col in df.columns if '日期' in col or 'date' in col.lower() or 'time' in col.lower()]
        if not date_columns:
            print("未找到日期列，尝试使用第一列")
            date_column = df.columns[0]
        else:
            date_column = date_columns[0]
        
        print(f"使用的日期列: {date_column}")
        
        # 转换日期格式并筛选2019年数据
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df_2019 = df[df[date_column].dt.year == 2019].copy()
        
        print(f"2019年总投诉数量: {len(df_2019)}")
        return df_2019
        
    except Exception as e:
        print(f"读取文件错误: {e}")
        return None

def sample_complaints(df, sample_size=1000, seed=42):
    """随机抽取指定数量的投诉"""
    if len(df) < sample_size:
        print(f"警告: 数据量不足{sample_size}条，实际只有{len(df)}条")
        sample_size = len(df)
    
    # 随机抽样
    sampled_df = df.sample(n=sample_size, random_state=seed, replace=False)
    return sampled_df

def check_sales_related(complaint_text):
    """使用API判断投诉是否与销售相关"""
    # 预处理文本，避免过长
    if len(complaint_text) > 2000:
        complaint_text = complaint_text[:2000] + "..."
    
    prompt = f"""
请分析以下消费者投诉内容，判断是否与销售相关问题相关：
"{complaint_text}"

销售相关问题包括：虚假宣传、误导销售、强制销售、价格欺诈、未明码标价、销售不合格产品、夸大产品效果等。

请用以下JSON格式回复：
{{
    "is_sales_related": true/false,
    "category": "具体类别",
    "reason": "判断理由",
    "confidence": "高/中/低"
}}

请确保回复是有效的JSON格式，不要包含其他内容。
"""
    try:
        response = client.chat.completions.create(
            model="Pro/deepseek-ai/DeepSeek-V3",
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API调用错误: {e}")
        return json.dumps({"error": str(e), "is_sales_related": False})

def process_complaints_batch(complaints_df, start_index=0, batch_size=20):
    """分批处理投诉数据，支持断点续跑"""
    
    # 使用任务ID避免冲突
    progress_file = f'processing_progress_{TASK_ID}.txt'
    total = len(complaints_df)
    
    # 检查是否存在进度文件
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            start_index = int(f.read().strip())
        print(f"从断点继续处理，起始索引: {start_index}")
    
    results = []
    
    for i in range(start_index, total):
        # 自动检测投诉内容列名
        content_columns = [col for col in complaints_df.columns if '内容' in col or 'content' in col.lower() or 'complaint' in col.lower()]
        if not content_columns:
            content_column = complaints_df.columns[1]  # 假设第二列是内容
        else:
            content_column = content_columns[0]
        
        complaint_text = str(complaints_df.iloc[i][content_column])
        
        print(f"处理第 {i+1}/{total} 条投诉...")
        
        # 调用API分析
        result = check_sales_related(complaint_text)
        
        # 解析API响应
        try:
            result_data = json.loads(result)
        except:
            result_data = {"raw_response": result, "is_sales_related": False}
        
        # 保存结果
        results.append({
            'index': i,
            'complaint_content': complaint_text,
            'is_sales_related': result_data.get('is_sales_related', False),
            'category': result_data.get('category', ''),
            'reason': result_data.get('reason', ''),
            'confidence': result_data.get('confidence', ''),
            'raw_response': result,
            'processed_time': pd.Timestamp.now()
        })
        
        # 每处理batch_size条保存一次
        if (i + 1) % batch_size == 0 or (i + 1) == total:
            save_interim_results(results, i + 1)
            print(f"已保存批次结果，当前进度: {i+1}/{total}")
            results = []  # 清空结果列表
        
        # 更新进度
        with open(progress_file, 'w', encoding='utf-8') as f:
            f.write(str(i + 1))
        
        # 添加延迟避免API限制
        time.sleep(1)
    
    # 处理完成后删除进度文件
    if os.path.exists(progress_file):
        os.remove(progress_file)
        print("任务完成，进度文件已删除")
    
    return True

def save_interim_results(results, current_index):
    """保存中间结果"""
    output_file = f'sales_complaints_analysis_{TASK_ID}.xlsx'
    
    # 创建DataFrame
    df_results = pd.DataFrame(results)
    
    # 如果文件已存在，读取现有数据并追加
    if os.path.exists(output_file):
        try:
            existing_df = pd.read_excel(output_file)
            df_results = pd.concat([existing_df, df_results], ignore_index=True)
        except Exception as e:
            print(f"读取现有文件失败，创建新文件: {e}")
    
    # 保存到Excel
    try:
        df_results.to_excel(output_file, index=False, engine='openpyxl')
        print(f"已保存第 {current_index} 条结果到 {output_file}")
    except Exception as e:
        print(f"保存Excel失败: {e}")
        # 备用方案：保存为CSV
        csv_file = f'sales_complaints_analysis_{TASK_ID}.csv'
        df_results.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"已保存第 {current_index} 条结果到 {csv_file}")

def main():
    """主函数"""
    input_csv = "/Users/chenyaxin/Desktop/投诉内容汇总.csv"
    
    # 步骤1: 筛选2019年数据
    print("正在筛选2019年投诉数据...")
    df_2019 = filter_2019_complaints(input_csv)
    
    if df_2019 is None or len(df_2019) == 0:
        print("未找到2019年投诉数据，请检查文件格式和日期列")
        return
    
    # 步骤2: 随机抽取1000条
    print("正在随机抽样...")
    sampled_df = sample_complaints(df_2019, 1000)
    
    # 保存抽样结果
    sampled_output = f"/Users/chenyaxin/Desktop/sampled_2019_complaints_{TASK_ID}.xlsx"
    sampled_df.to_excel(sampled_output, index=False)
    print(f"已保存抽样数据到 {sampled_output}")
    print(f"抽样数据形状: {sampled_df.shape}")
    
    # 步骤3: 分批处理并分析（减小批次大小避免API压力）
    print("开始分析销售相关投诉...")
    process_complaints_batch(sampled_df, batch_size=20)

if __name__ == "__main__":
    main()