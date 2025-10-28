import pandas as pd
import random
import os
import time
import json
import re
from openai import OpenAI
import uuid

# 初始化API客户端
client = OpenAI(
    api_key="sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol", 
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
        
        # 直接指定日期列名
        date_column = '发布时间'
        
        if date_column not in df.columns:
            print(f"错误: 未找到列 '{date_column}'")
            print("可用列:", df.columns.tolist())
            return None
        
        print(f"使用的日期列: {date_column}")
        
        # 转换日期格式并筛选2019年数据
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # 检查转换后的日期情况
        null_dates = df[date_column].isna().sum()
        if null_dates > 0:
            print(f"警告: 有 {null_dates} 条记录的日期无法解析")
        
        # 筛选2019年数据
        df_2019 = df[df[date_column].dt.year == 2019].copy()
        
        print(f"2019年总投诉数量: {len(df_2019)}")
        
        # 显示日期范围以供验证
        if len(df_2019) > 0:
            min_date = df_2019[date_column].min()
            max_date = df_2019[date_column].max()
            print(f"2019年数据日期范围: {min_date} 到 {max_date}")
        
        return df_2019
        
    except Exception as e:
        print(f"读取文件错误: {e}")
        import traceback
        print(traceback.format_exc())
        return None
    
def sample_complaints(df, sample_size=100, seed=42):
    """随机抽取指定数量的投诉"""
    if len(df) < sample_size:
        print(f"警告: 数据量不足{sample_size}条，实际只有{len(df)}条")
        sample_size = len(df)
    
    # 随机抽样
    sampled_df = df.sample(n=sample_size, random_state=seed, replace=False)
    return sampled_df

def safe_json_parse(json_string, max_retries=3):
    """安全解析JSON，包含多重保护机制"""
    if not json_string or json_string.strip() == "":
        return create_default_response("空响应")
    
    # 清理JSON字符串
    cleaned_json = json_string.strip()
    
    # 尝试直接解析
    for attempt in range(max_retries):
        try:
            parsed_data = json.loads(cleaned_json)
            # 验证基本结构
            if isinstance(parsed_data, dict):
                return parsed_data
            else:
                raise json.JSONDecodeError("响应不是JSON对象", cleaned_json, 0)
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                # 尝试不同的清理策略
                cleaned_json = clean_json_response(cleaned_json, attempt)
            else:
                print(f"JSON解析失败 (尝试{attempt+1}次): {e}")
                print(f"原始响应: {json_string}")
                return extract_json_with_regex(json_string)

def clean_json_response(json_string, strategy):
    """使用不同策略清理JSON响应"""
    if strategy == 0:
        # 策略1: 移除可能的Markdown代码块标记
        cleaned = re.sub(r'^```json\s*|\s*```$', '', json_string, flags=re.IGNORECASE)
        return cleaned.strip()
    elif strategy == 1:
        # 策略2: 提取第一个{到最后一个}之间的内容
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', json_string, re.DOTALL)
        if match:
            return match.group(0)
        return json_string
    else:
        # 策略3: 修复常见的JSON格式问题
        cleaned = json_string
        # 修复单引号问题
        cleaned = re.sub(r"(?<!\\)'", '"', cleaned)
        # 修复缺少引号的键
        cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)
        # 修复尾随逗号
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        return cleaned

def extract_json_with_regex(response_text):
    """使用正则表达式从响应中提取JSON结构"""
    try:
        # 尝试提取完整的JSON对象
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        if matches:
            # 选择最长的匹配（可能是最完整的）
            best_match = max(matches, key=len)
            return json.loads(best_match)
        
        # 如果找不到完整JSON，尝试手动构建
        return build_response_from_text(response_text)
    except Exception as e:
        print(f"正则提取也失败: {e}")
        return create_default_response(f"正则提取失败: {str(e)}")

def build_response_from_text(text):
    """从文本内容手动构建响应结构"""
    # 初始化默认响应
    response = create_default_response("手动解析")
    
    try:
        # 尝试提取关键信息
        text_lower = text.lower()
        
        # 判断是否相关
        if 'true' in text_lower or '相关' in text_lower or '是' in text_lower:
            response['is_policy_related'] = True
        elif 'false' in text_lower or '不相关' in text_lower or '否' in text_lower:
            response['is_policy_related'] = False
        
        # 提取类别
        category_match = re.search(r'category["\':\s]+([^",}\'\n]+)', text, re.IGNORECASE)
        if category_match:
            response['category'] = category_match.group(1).strip()
        
        # 提取理由
        reason_match = re.search(r'reason["\':\s]+([^",}\'\n]+)', text, re.IGNORECASE)
        if reason_match:
            response['reason'] = reason_match.group(1).strip()
        
        # 提取置信度
        confidence_match = re.search(r'confidence["\':\s]+([^",}\'\n]+)', text, re.IGNORECASE)
        if confidence_match:
            confidence = confidence_match.group(1).strip()
            if confidence in ['高', '中', '低']:
                response['confidence'] = confidence
        
        return response
        
    except Exception as e:
        print(f"手动解析失败: {e}")
        return create_default_response("手动解析失败")

def create_default_response(error_reason):
    """创建默认的响应结构"""
    return {
        "is_policy_related": False,
        "category": f"解析错误-{error_reason}",
        "reason": f"JSON解析失败: {error_reason}",
        "confidence": "低"
    }

def check_policy_related(complaint_text):
    """使用API判断投诉是否与金融营销宣传政策相关"""
    if len(complaint_text) > 2000:
        complaint_text = complaint_text[:2000] + "..."
    
    prompt = f"""
请分析以下消费者投诉内容，判断是否与《关于进一步规范金融营销宣传行为的通知》中禁止的营销宣传行为相关。

【重要说明】
- 该政策主要规范金融营销宣传行为，不包括贷后催收行为
- 如果投诉主要涉及催收问题（如电话催收、上门催收、骚扰亲友等），请直接返回不相关
- 只有涉及营销推广、产品销售等宣传行为才属于政策范围

政策禁止的营销宣传行为包括：
- 非法或超范围开展营销：无证经营、超范围宣传
- 欺诈或引人误解：虚假宣传、夸大效果、隐瞒限制条件、承诺保本保收益
- 损害公平竞争：诋毁竞争对手、不当评比
- 利用政府公信力：利用监管审核程序误导消费者
- 损害消费者知情权：未醒目披露信息、未明码标价、关键信息隐藏
- 利用互联网进行不当营销：无法一键关闭的弹窗、未经审核的营销信息
- 违规发送营销信息：未经同意的营销电话、营销短信、营销邮件推送
- 其他违法违规营销活动

投诉内容：
"{complaint_text}"

请用以下JSON格式回复，确保格式完全正确：
{{
    "is_policy_related": true或false,
    "category": "如果不相关请填具体原因如'催收行为'，如果相关请填写具体的禁止行为类别",
    "reason": "判断理由，明确说明是否属于营销宣传行为",
    "confidence": "高/中/低"
}}

重要：请确保只返回有效的JSON格式，不要包含任何其他文字、注释或Markdown标记。
"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1
        )
        
        raw_response = response.choices[0].message.content
        print(f"API原始响应: {raw_response}")  # 调试信息
        
        # 使用安全的JSON解析
        result_data = safe_json_parse(raw_response)
        
        # 验证必要字段
        required_fields = ['is_policy_related', 'category', 'reason', 'confidence']
        for field in required_fields:
            if field not in result_data:
                result_data[field] = create_default_response("字段缺失")[field]
                print(f"警告: 缺少字段 {field}，使用默认值")
        
        # 确保布尔值类型正确
        if isinstance(result_data['is_policy_related'], str):
            str_value = result_data['is_policy_related'].lower()
            result_data['is_policy_related'] = str_value == 'true'
        
        return result_data  # 直接返回字典，不再转换为JSON字符串
        
    except Exception as e:
        print(f"API调用错误: {e}")
        error_response = create_default_response(f"API错误: {str(e)}")
        return error_response

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
        
        # 调用API分析 - 现在直接返回字典
        result_data = check_policy_related(complaint_text)
        
        # 保存结果
        results.append({
            'index': i,
            'complaint_content': complaint_text[:500] + "..." if len(complaint_text) > 500 else complaint_text,  # 截断长文本
            'is_policy_related': result_data.get('is_policy_related', False),
            'policy_category': result_data.get('category', ''),
            'policy_reason': result_data.get('reason', ''),
            'confidence_level': result_data.get('confidence', ''),
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
    output_file = f'policy_complaints_analysis_{TASK_ID}.xlsx'
    
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
        csv_file = f'policy_complaints_analysis_{TASK_ID}.csv'
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
    
    # 步骤2: 随机抽取100条
    print("正在随机抽样...")
    sampled_df = sample_complaints(df_2019, 100)
    
    # 保存抽样结果
    sampled_output = f"/Users/chenyaxin/Desktop/sampled_2019_complaints_{TASK_ID}.xlsx"
    sampled_df.to_excel(sampled_output, index=False)
    print(f"已保存抽样数据到 {sampled_output}")
    print(f"抽样数据形状: {sampled_df.shape}")
    
    # 步骤3: 分批处理并分析
    print("开始分析政策相关投诉...")
    process_complaints_batch(sampled_df, batch_size=20)

if __name__ == "__main__":
    main()