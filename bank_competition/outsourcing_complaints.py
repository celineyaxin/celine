import pandas as pd
from openai import OpenAI
import time
import re

# 初始化OpenAI客户端
client = OpenAI(
    api_key="sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol", 
    base_url="https://api.siliconflow.cn/v1"
)

def analyze_complaint_text(complaint_text):
    """
    分析单条投诉内容是否与银行外包业务相关
    
    Args:
        complaint_text (str): 投诉内容文本
        
    Returns:
        dict: 包含分析结果各个部分的字典
    """
    if pd.isna(complaint_text) or not complaint_text.strip():
        return {
            "是否涉及外包业务": "否",
            "外包业务类型": "无",
            "外包问题类型": "无",
            "涉及部门": "无",
            "外包公司": "无",
            "关键理由": "文本为空或无效",
            "分析状态": "跳过"
        }
    
    # 构建针对外包业务分析的提示词
    prompt = f"""
您是一名资深银行合规与风险管理专家，请分析以下银行客户投诉内容，判断是否涉及银行的外包业务及相关问题。

### 分析要求：
请仔细阅读投诉内容，识别以下信息：

1.  **是否涉及外包业务**：
    - 投诉中是否提到银行将业务外包给第三方机构？
    - 是否有迹象表明服务由非银行员工提供？
    - 是否提及外部公司、合作方或服务商？

2.  **外包业务类型**（如适用）：
    - 催收业务
    - 电话营销
    - 客户服务
    - 技术支持
    - 数据处理
    - 其他外包业务

3.  **外包问题类型**（如适用）：
    - 服务态度问题
    - 信息安全问题
    - 违规操作
    - 虚假宣传
    - 骚扰行为
    - 其他问题

4.  **涉及部门**（如适用）：
    - 信用卡中心
    - 个人贷款部门
    - 财富管理部门
    - 数字银行部
    - 其他部门

5.  **外包公司**（如适用）：
    - 如果提到具体外包公司名称，请列出

6.  **关键理由**：
    - 简要解释判断的依据，引用文本中的关键描述

### 请按照以下格式输出分析结果：
是否涉及外包业务: 【是】/【否】/【不确定】
外包业务类型: [类型1, 类型2, ...]
外包问题类型: [问题1, 问题2, ...]
涉及部门: [部门1, 部门2, ...]
外包公司: [公司1, 公司2, ...]
关键理由: [简要解释]

### 投诉内容：
{complaint_text}

### 请开始您的分析：
"""
    
    try:
        # 创建对话请求
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": "你是一名严谨的银行合规分析专家，擅长从投诉内容中识别外包业务相关问题。请严格按照用户要求的格式输出结果。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # 低温度值使输出更加确定性
            stream=False
        )
        
        # 解析模型的回复
        analysis_result = response.choices[0].message.content
        return parse_analysis_result(analysis_result)
        
    except Exception as e:
        print(f"API调用出错: {e}")
        return {
            "是否涉及外包业务": "错误",
            "外包业务类型": "无",
            "外包问题类型": "无",
            "涉及部门": "无",
            "外包公司": "无",
            "关键理由": f"API调用失败: {str(e)}",
            "分析状态": "失败"
        }

def parse_analysis_result(result_text):
    """
    解析模型返回的分析结果文本为结构化数据
    
    Args:
        result_text (str): 模型返回的分析结果文本
        
    Returns:
        dict: 结构化的分析结果
    """
    # 初始化默认值
    parsed_result = {
        "是否涉及外包业务": "不确定",
        "外包业务类型": "无",
        "外包问题类型": "无",
        "涉及部门": "无",
        "外包公司": "无",
        "关键理由": "未能解析结果",
        "分析状态": "成功"
    }
    
    try:
        # 使用正则表达式提取各个部分
        outsourcing_match = re.search(r"是否涉及外包业务[：:]\s*【?(是|否|不确定)】?", result_text)
        
        # 提取外包业务类型
        biz_type_match = re.search(r"外包业务类型[：:]\s*\[([^\]]+)\]", result_text)
        if biz_type_match:
            parsed_result["外包业务类型"] = biz_type_match.group(1).strip()
        
        # 提取外包问题类型
        problem_match = re.search(r"外包问题类型[：:]\s*\[([^\]]+)\]", result_text)
        if problem_match:
            parsed_result["外包问题类型"] = problem_match.group(1).strip()
        
        # 提取涉及部门
        dept_match = re.search(r"涉及部门[：:]\s*\[([^\]]+)\]", result_text)
        if dept_match:
            parsed_result["涉及部门"] = dept_match.group(1).strip()
        
        # 提取外包公司
        company_match = re.search(r"外包公司[：:]\s*\[([^\]]+)\]", result_text)
        if company_match:
            parsed_result["外包公司"] = company_match.group(1).strip()
        
        # 提取关键理由
        reason_match = re.search(r"关键理由[：:]\s*(.+)", result_text)
        if reason_match:
            parsed_result["关键理由"] = reason_match.group(1).strip()
        
        # 更新解析结果
        if outsourcing_match:
            parsed_result["是否涉及外包业务"] = outsourcing_match.group(1)
        
    except Exception as e:
        print(f"解析结果时出错: {e}")
        parsed_result["分析状态"] = "解析失败"
    
    return parsed_result

def process_csv_file(file_path, output_path):
    """
    处理CSV文件中的投诉数据
    
    Args:
        file_path (str): 输入CSV文件路径
        output_path (str): 输出Excel文件路径
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 检查必要的列是否存在
        if "投诉内容" not in df.columns:
            print("错误: CSV文件中未找到'投诉内容'列")
            return
        
        print(f"找到 {len(df)} 条投诉记录需要处理")
        
        # 添加分析结果列
        df["是否涉及外包业务"] = ""
        df["外包业务类型"] = ""
        df["外包问题类型"] = ""
        df["涉及部门"] = ""
        df["外包公司"] = ""
        df["关键理由"] = ""
        df["分析状态"] = ""
        
        # 逐条处理记录
        for index, row in df.iterrows():
            print(f"处理第 {index+1}/{len(df)} 条记录...")
            
            # 获取投诉内容文本
            complaint_text = row["投诉内容"]
            
            # 调用API进行分析
            result = analyze_complaint_text(complaint_text)
            
            # 将结果保存到DataFrame
            df.at[index, "是否涉及外包业务"] = result["是否涉及外包业务"]
            df.at[index, "外包业务类型"] = result["外包业务类型"]
            df.at[index, "外包问题类型"] = result["外包问题类型"]
            df.at[index, "涉及部门"] = result["涉及部门"]
            df.at[index, "外包公司"] = result["外包公司"]
            df.at[index, "关键理由"] = result["关键理由"]
            df.at[index, "分析状态"] = result["分析状态"]
            
            # 添加延迟，避免API速率限制
            time.sleep(1)
        
        # 保存结果到Excel文件
        df.to_excel(output_path, index=False)
        print(f"分析完成！结果已保存到: {output_path}")
        
        # 打印简要统计
        outsourcing_count = len(df[df["是否涉及外包业务"] == "是"])
        uncertain_count = len(df[df["是否涉及外包业务"] == "不确定"])
        print(f"\n分析统计:")
        print(f"- 涉及外包业务的投诉: {outsourcing_count}")
        print(f"- 不确定是否涉及外包的投诉: {uncertain_count}")
        print(f"- 不涉及外包的投诉: {len(df) - outsourcing_count - uncertain_count}")
        
        # 如果有涉及外包的投诉，打印外包业务类型分布
        if outsourcing_count > 0:
            print("\n外包业务类型分布:")
            biz_types = df[df["是否涉及外包业务"] == "是"]["外包业务类型"].value_counts()
            for biz_type, count in biz_types.items():
                print(f"- {biz_type}: {count}")
                
    except Exception as e:
        print(f"处理CSV文件时出错: {e}")

# 主程序
if __name__ == "__main__":
    input_file = "/Users/chenyaxin/Desktop/bank_complaints_stratified_sample.csv"  # 输入的CSV文件路径
    output_file = "/Users/chenyaxin/Desktop/外包业务分析结果投诉.xlsx"  # 输出的Excel文件路径
    
    print("开始处理银行投诉数据...")
    process_csv_file(input_file, output_file)