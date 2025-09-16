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
input_file = '/Users/chenyaxin/Desktop/再分类.csv'  # 输入文件名，请替换为您的实际文件路径
output_csv_file = '/Users/chenyaxin/Desktop/recruitment_keyword_qw.csv'  # 输出CSV文件名
output_excel_file = '/Users/chenyaxin/Desktop/recruitment_keyword_qw.xlsx'  # 输出Excel文件名

# 读取CSV文件并只保留指定列
columns_to_keep = ['企业名称', '招聘岗位', '职位描述', '学历要求', '招聘发布日期']
df = pd.read_csv(input_file)
df = df.dropna(how='all')
# df = pd.read_csv(input_file, nrows=1000)
# 检查并只保留存在的列
existing_columns = [col for col in columns_to_keep if col in df.columns]
df = df[existing_columns]

print(f"已保留以下列: {existing_columns}")

def create_prompt(job_description):
    prompt = f"""
您是一位专业的数据分析研究员，需要根据权威职业分类标准对招聘职位进行精确分类。请严格按照以下指令执行：

【任务】
判断给定的"职位描述"是否属于"数据处理与相关技术"类别。输出必须是数字 1（是） 或 0（否）。

【分类标准 - 必须严格遵守】
以下职业被定义为"数据处理与相关技术"类别。只要职位描述的核心工作任务与以下任意一类职业的主要工作任务重合，即应归类为 1。

核心数据处理与技术类职业：
1. 数据分析处理工程技术人员：数据规划、采集、管理、分析、挖掘、数据库设计与优化、数据资源整合、数据咨询服务
2. 大数据工程技术人员：大数据采集、清洗、分析、治理、挖掘、系统开发与运维
3. 人工智能工程技术人员/训练师：AI算法、机器学习、深度学习的研究开发、训练测试、应用与系统管理，包括数据标注、算法调优
4. 统计专业人员/职业信息分析专业人员：统计方案设计、数据采集整理、评估分析、预测预警、决策咨询
5. 数字化解决方案设计师/数字化管理师：数字化需求分析、业务流程设计、技术解决方案、大数据决策分析、在线协同管理
6. 区块链工程技术人员：区块链架构设计、密码学算法、共识机制、智能合约等底层技术开发
7. 网络与信息安全管理员/电子数据取证分析师：网络安全防护、数据安全合规审查、电子数据提取、恢复、分析
8. 信用管理师：征信数据服务、信用信息分析、信用评价、模型开发、数据治理
9. 商务数据分析师：商务数据采集、清洗、挖掘、分析，指标体系构建，数据建模，分析报告
10. 电子商务师：仅当明确包含"数据采集和销售数据分析"或"商务网站数据架构设计"时

【不属于1的情况（应归类为0） - 必须严格遵守】
*   **通用职能岗位**：如行政、人事、财务、法务、普通文员等。
*   **传统销售与市场岗位**：工作内容以达成销售交易、客户关系维护、品牌宣传、市场活动策划为主，即使提及“数据分析”，也仅是简单使用Excel报表或第三方工具查看基础结果，而非**核心职责**。
*   **传统工程技术岗位**：如硬件开发、机械设计、电气工程等。
*   **战略与管理咨询岗位**：工作内容以提供宏观的战略建议、管理优化方案为主，虽可能使用数据作为支撑，但其核心技能并非数据处理技术本身（如：**科技咨询师**虽涉及信息分析，但更偏向情报和宏观咨询，故不属于1）。
*   **科学研究与实验分析岗位**：**【新增项】即使工作描述涉及数据分析并与“统计专业人员”的任务有表面重合，但如果其核心任务是分析实验数据（如生物实验数据、化学检测数据、材料物理性能数据、心理学实验数据等），旨在得出科学结论而非构建数据系统或提供通用商业决策支持，则不属于本类别。**
*   **其他**：工作描述中完全不含数据处理、分析、管理或相关系统开发、算法应用等关键词的岗位。

【增强判断逻辑】
1.  **关键词与实质任务匹配**：寻找是否包含以下**核心关键词**及其所代表的**实质性任务**：
    *   **数据操作**：数据采集、清洗、治理、管理、整合、处理。
    *   **数据分析**：数据分析、数据挖掘、数据建模、机器学习、统计分析、量化分析、商业分析（需具体）、预测预警。
    *   **数据系统**：数据库设计/优化/维护、数据仓库、数据平台、数据服务应用编程、数据指标体系构建。
    *   **数据应用**：数据可视化、数据报告、决策支持、数据咨询服务。
    *   **算法与安全**：算法开发/训练/测试、人工智能、数据安全、电子数据取证。
2.  **核心重合判断**：将提取的任务与上述10类职业的核心任务进行比对。**只要核心任务重合，即输出1**。不要因为职位名称或公司行业而主观臆断。
3.  **果断排除**：如果任务属于上述“不属于1的情况”，则输出0。

【输出格式】
仅输出JSON格式结果：
{{
  "classification_result": 1或0,
  "reasoning": "简要分类理由，如：该职位涉及数据挖掘与系统开发，与'大数据工程技术人员'核心任务重合；或：该职位虽涉及数据分析，但核心是处理实验数据，属于科学研究范畴。"
}}

请对以下职位描述进行分类：
{job_description}
"""
    return prompt

# 调用模型函数 - 使用硅基流动的API格式
def ask_model(prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                # model="deepseek-ai/DeepSeek-V3",  # 使用您指定的模型
                model="Qwen/Qwen3-32B", 
                messages=[
                    {"role": "system", "content": "你是一位专业的金融数据分析研究员，正在研究企业数据密集度。"},
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
if 'classification_result' not in df.columns:
    df['classification_result'] = None
if 'reasoning' not in df.columns:
    df['reasoning'] = None

# 分块处理数据
chunk_size = 50  # 每50条写入一次
total_rows = len(df)

# 创建进度条
with tqdm(total=total_rows, desc="处理进度") as pbar:
    for start_idx in range(0, total_rows, chunk_size):
        end_idx = min(start_idx + chunk_size, total_rows)
        
        # 处理当前块
        for idx in range(start_idx, end_idx):
            if pd.isna(df.at[idx, 'classification_result']):  # 只处理尚未处理的行
                # 假设CSV中有'职位描述'列，如果没有请修改为实际的列名
                description = df.at[idx, '职位描述']
                prompt = create_prompt(description)
                response_text = ask_model(prompt)
                
                # 初始化默认值
                classification_result = 0
                reasoning = "无法判断或API调用失败"
                
                if response_text:
                    try:
                        # 尝试解析JSON响应
                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = response_text[json_start:json_end]
                            response_json = json.loads(json_str)
                            classification_result = response_json.get('classification_result', 0)
                            reasoning = response_json.get('reasoning', '无理由提供')
                        else:
                            # 如果没有找到JSON，尝试手动解析
                            if "1" in response_text or "是" in response_text or "true" in response_text.lower():
                                classification_result = 1
                            reasoning = response_text  # Fallback: 使用整个响应作为理由
                    except json.JSONDecodeError:
                        # 如果JSON解析失败，尝试手动解析
                        if "1" in response_text or "是" in response_text or "true" in response_text.lower():
                            classification_result = 1
                        reasoning = response_text  # Fallback: 使用整个响应作为理由
                
                df.at[idx, 'classification_result'] = classification_result
                df.at[idx, 'reasoning'] = reasoning
                
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

# 统计分类结果
data_related_count = df['classification_result'].sum()
total_count = len(df)
print(f"\n分类结果统计:")
print(f"数据处理相关岗位: {data_related_count} ({data_related_count/total_count*100:.2f}%)")
print(f"非数据处理岗位: {total_count - data_related_count} ({(total_count - data_related_count)/total_count*100:.2f}%)")

# 显示一些处理后的数据样本
print("\n处理后的数据样本:")
print(df.head())

# 可选：询问是否删除CSV文件
delete_csv = input("是否删除临时的CSV文件？(y/n): ")
if delete_csv.lower() == 'y':
    import os
    os.remove(output_csv_file)
    print(f"已删除临时文件 {output_csv_file}")
else:
    print(f"CSV文件已保留: {output_csv_file}")
print("处理完成!")