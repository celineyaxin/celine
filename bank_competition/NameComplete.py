import pandas as pd
import openai
import time
import re
import os

# 设置API配置
client = openai.OpenAI(
    api_key="sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol", 
    base_url="https://api.siliconflow.cn/v1"
)

def get_company_full_name_with_confidence(short_name):
    """
    使用LLM获取公司全称和置信度
    
    参数:
    short_name: 公司简称
    
    返回:
    tuple: (全称, 置信度等级, 备注)
    """
    prompt = f"""
    你是一个金融数据专家。请将以下金融机构的简称或非正式名称转换为官方全称，并给出置信度等级（低、中、高）。

    请严格按照以下格式回复，不要添加任何其他内容：
    全称: [官方全称]
    置信度: [低/中/高]
    备注: [简要说明匹配依据]

    示例：
    输入: "工行"
    输出:
    全称: 中国工商银行股份有限公司
    置信度: 高
    备注: 这是中国工商银行的通用简称

    输入: "某地方银行"
    输出:
    全称: 未知
    置信度: 低
    备注: 无法确定具体指哪家地方银行

    现在请处理："{short_name}"
    """
    
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-32B",
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 解析响应
        full_name = "未知"
        confidence = "低"
        remark = "解析失败"
        
        # 提取全称
        full_name_match = re.search(r'全称:\s*(.+)', result_text)
        if full_name_match:
            full_name = full_name_match.group(1).strip()
        
        # 提取置信度
        confidence_match = re.search(r'置信度:\s*(低|中|高)', result_text)
        if confidence_match:
            confidence = confidence_match.group(1)
        
        # 提取备注
        remark_match = re.search(r'备注:\s*(.+)', result_text)
        if remark_match:
            remark = remark_match.group(1).strip()
        
        return full_name, confidence, remark
        
    except Exception as e:
        print(f"API调用失败: {str(e)}")
        return "API错误", "低", f"调用失败: {str(e)}"

def process_company_names_with_llm(input_file, output_file, name_column='机构名称', batch_delay=1):
    """
    使用LLM处理公司名称，生成全称和置信度
    
    参数:
    input_file: 输入文件路径
    output_file: 输出文件路径
    name_column: 包含机构名称的列名
    batch_delay: 批处理延迟时间（秒）
    """
    
    try:
        # 读取Excel文件
        print("正在读取Excel文件...")
        df = pd.read_excel(input_file)
        
        # 检查指定列是否存在
        if name_column not in df.columns:
            available_columns = ', '.join(df.columns.tolist())
            raise ValueError(f"列 '{name_column}' 不存在。可用列: {available_columns}")
        
        # 检查是否已有处理进度
        temp_file = output_file.replace('.xlsx', '_temp.xlsx')
        start_index = 0
        
        if os.path.exists(temp_file):
            print("检测到临时文件，从上次中断处继续...")
            temp_df = pd.read_excel(temp_file)
            start_index = len(temp_df)
            df = temp_df  # 使用已处理的数据
        else:
            # 初始化新列
            df['模型生成全称'] = ""
            df['置信度'] = ""
            df['匹配备注'] = ""
        
        total_count = len(df)
        print(f"开始处理 {total_count} 个机构名称，从第 {start_index+1} 个开始...")
        
        # 处理每个机构名称（从上次中断处开始）
        for idx in range(start_index, total_count):
            row = df.iloc[idx]
            short_name = row[name_column]
            print(f"处理进度: {idx+1}/{total_count} - {short_name}")
            
            # 调用LLM获取全称和置信度
            full_name, confidence, remark = get_company_full_name_with_confidence(short_name)
            
            # 更新DataFrame
            df.at[idx, '模型生成全称'] = full_name
            df.at[idx, '置信度'] = confidence
            df.at[idx, '匹配备注'] = remark
            
            # 每处理5个保存一次进度
            if (idx + 1) % 5 == 0:
                print(f"已处理 {idx+1} 个，保存进度...")
                df.to_excel(temp_file, index=False)
            
            # 控制API调用频率
            if (idx + 1) % 5 == 0:
                print(f"已处理 {idx+1} 个，暂停 {batch_delay} 秒...")
                time.sleep(batch_delay)
        
        # 保存最终结果
        print("正在保存最终结果到Excel...")
        df.to_excel(output_file, index=False)
        
        # 删除临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print("临时文件已删除")
        
        # 生成统计信息
        high_count = len(df[df['置信度'] == "高"])
        medium_count = len(df[df['置信度'] == "中"])
        low_count = len(df[df['置信度'] == "低"])
        
        print(f"\n处理完成!")
        print(f"总处理数量: {total_count}")
        print(f"高置信度: {high_count}")
        print(f"中置信度: {medium_count}")
        print(f"低置信度: {low_count}")
        print(f"结果已保存到: {output_file}")
        
        return df
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        print("进度已保存到临时文件，下次运行将从断点继续")
        return None

def main():
    """
    主函数
    """
    # 文件路径配置
    input_file = "/Users/chenyaxin/Desktop/机构名称频率统计_增强版.xlsx"
    output_file = "/Users/chenyaxin/Desktop/机构名称全称匹配结果.xlsx"
    
    print("开始处理机构名称全称匹配...")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    print("-" * 50)
    
    # 执行处理
    result_df = process_company_names_with_llm(
        input_file=input_file,
        output_file=output_file,
        name_column='机构名称',
        batch_delay=1
    )
    
    if result_df is not None:
        # 显示低置信度的结果
        low_confidence_df = result_df[result_df['置信度'] == "低"]
        if len(low_confidence_df) > 0:
            print(f"\n低置信度项目 ({len(low_confidence_df)}个):")
            print(low_confidence_df[['机构名称', '模型生成全称', '置信度']].head(10))

if __name__ == "__main__":
    main()