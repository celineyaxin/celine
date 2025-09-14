import pandas as pd
from openai import OpenAI
import time
import re

# 初始化OpenAI客户端
client = OpenAI(
    api_key="YOUR_API_KEY_FROM_CLOUD_SILICONFLOW_CN", 
    base_url="https://api.siliconflow.cn/v1"
)

def analyze_penalty_text(penalty_text):
    """
    分析单条行政处罚文本是否与信息科技外包相关
    
    Args:
        penalty_text (str): 行政处罚决定书的违法事实描述文本
        
    Returns:
        dict: 包含分析结果各个部分的字典
    """
    if pd.isna(penalty_text) or not penalty_text.strip():
        return {
            "判断结果": "不相关",
            "置信度": "高",
            "关键理由": "文本为空或无效",
            "风险提示": "无",
            "分析状态": "跳过"
        }
    
    # 构建精细化的提示词
    prompt = f"""
您是一名资深金融监管专家，专注于信息科技风险管理。请根据《银行保险机构信息科技外包风险监管办法》及相关监管精神，对以下行政处罚决定书的【违法事实】描述进行专业分析。

### 分析背景：
信息科技外包风险通常间接表现为以下结果：
1.  **数据安全与泄露**：因第三方处理客户信息不当导致
2.  **系统中断与稳定性**：因外包运维或核心系统依赖第三方引发
3.  **内部控制失效**：对第三方合作机构管理缺失，准入、监控、退出机制不健全
4.  **业务连续性风险**：过度依赖单一外包服务商且无有效备份
5.  **网络安全管理**：外包人员违规操作或接入带来安全漏洞

### 待分析文本：
【处罚文本内容】：{penalty_text}

### 分析要求：
请严格按照以下结构和维度输出分析结果：

1.  **判断结果**：
    - 【相关】：文本明确提及或强烈暗示问题源于外部第三方服务商、科技公司、合作方等。
    - 【不相关】：文本明确显示为内部管理、自有员工、自有系统问题，与第三方无关。
    - 【不确定】：文本信息模糊，无法明确判断是否涉及第三方，但存在可能性。

2.  **置信度**（基于文本描述的清晰程度）：
    - 【高】：文本中出现"外包"、"第三方"、"服务商"、"合作机构"、"科技公司"等关键词，或明确描述责任方非银行自身。
    - 【中】：文本描述的问题类型（如数据泄露、系统宕机）通常与外包高度相关，但未明确提及第三方。
    - 【低】：文本信息过于简略或模糊，难以建立直接关联。

3.  **关键理由**：
    - 引用文本中的具体关键词或描述片段。
    - 简要解释这些描述为何指向（或不指向）外包风险。

4.  **风险提示**（如果判断为"相关"或"不确定"）：
    - 推断最可能涉及的外包风险类型（如：数据安全、系统稳定性、第三方准入管理、应急处置不力等）。
    - 简要说明理由。

### 请开始您的分析（请严格按照上述4点结构输出）：
"""
    
    try:
        # 创建对话请求
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {"role": "system", "content": "你是一名严谨的金融监管分析专家，擅长从文本中推断深层风险原因。请严格按照用户要求的结构输出结果。"},
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
            "判断结果": "错误",
            "置信度": "无",
            "关键理由": f"API调用失败: {str(e)}",
            "风险提示": "无",
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
        "判断结果": "不确定",
        "置信度": "低",
        "关键理由": "未能解析结果",
        "风险提示": "无",
        "分析状态": "成功"
    }
    
    try:
        # 使用正则表达式提取各个部分
        judgment_match = re.search(r"判断结果[：:]\s*【?(相关|不相关|不确定)】?", result_text)
        confidence_match = re.search(r"置信度[：:]\s*【?(高|中|低)】?", result_text)
        
        # 提取关键理由
        reason_start = result_text.find("关键理由")
        risk_start = result_text.find("风险提示")
        
        if reason_start != -1 and risk_start != -1:
            reason_text = result_text[reason_start:risk_start].replace("关键理由", "").strip("：: \n")
        elif reason_start != -1:
            reason_text = result_text[reason_start:].replace("关键理由", "").strip("：: \n")
        else:
            reason_text = "未能提取关键理由"
        
        # 提取风险提示
        if risk_start != -1:
            risk_text = result_text[risk_start:].replace("风险提示", "").strip("：: \n")
        else:
            risk_text = "无"
        
        # 更新解析结果
        if judgment_match:
            parsed_result["判断结果"] = judgment_match.group(1)
        if confidence_match:
            parsed_result["置信度"] = confidence_match.group(1)
        
        parsed_result["关键理由"] = reason_text
        parsed_result["风险提示"] = risk_text
        
    except Exception as e:
        print(f"解析结果时出错: {e}")
        parsed_result["分析状态"] = "解析失败"
    
    return parsed_result

def process_excel_file(file_path, output_path):
    """
    处理Excel文件中的行政处罚数据
    
    Args:
        file_path (str): 输入Excel文件路径
        output_path (str): 输出Excel文件路径
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 检查必要的列是否存在
        if "主要违法违规事实" not in df.columns:
            print("错误: Excel文件中未找到'主要违法违规事实'列")
            return
        
        print(f"找到 {len(df)} 条记录需要处理")
        
        # 添加分析结果列
        df["外包相关判断"] = ""
        df["判断置信度"] = ""
        df["关键理由"] = ""
        df["风险提示"] = ""
        df["分析状态"] = ""
        
        # 逐条处理记录
        for index, row in df.iterrows():
            print(f"处理第 {index+1}/{len(df)} 条记录...")
            
            # 获取违法违规事实文本
            penalty_text = row["主要违法违规事实"]
            
            # 调用API进行分析
            result = analyze_penalty_text(penalty_text)
            
            # 将结果保存到DataFrame
            df.at[index, "外包相关判断"] = result["判断结果"]
            df.at[index, "判断置信度"] = result["置信度"]
            df.at[index, "关键理由"] = result["关键理由"]
            df.at[index, "风险提示"] = result["风险提示"]
            df.at[index, "分析状态"] = result["分析状态"]
            
            # 添加延迟，避免API速率限制
            time.sleep(1)
        
        # 保存结果到新的Excel文件
        df.to_excel(output_path, index=False)
        print(f"分析完成！结果已保存到: {output_path}")
        
        # 打印简要统计
        related_count = len(df[df["外包相关判断"] == "相关"])
        uncertain_count = len(df[df["外包相关判断"] == "不确定"])
        print(f"\n分析统计:")
        print(f"- 相关记录: {related_count}")
        print(f"- 不确定记录: {uncertain_count}")
        print(f"- 不相关记录: {len(df) - related_count - uncertain_count}")
        
    except Exception as e:
        print(f"处理Excel文件时出错: {e}")

# 主程序
if __name__ == "__main__":
    input_file = "提取所属公司.xlsx"  # 输入的Excel文件路径
    output_file = "提取所属公司_分析结果.xlsx"  # 输出的Excel文件路径
    
    print("开始处理行政处罚数据...")
    process_excel_file(input_file, output_file)