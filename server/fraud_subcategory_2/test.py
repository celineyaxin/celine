from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re
import json
import os

client = OpenAI(api_key="sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol", base_url="https://api.siliconflow.cn/v1")

# 修改为Excel文件路径
excel_file = '/Users/chenyaxin/Desktop/cleaned.xlsx'
output_file = '/Users/chenyaxin/Desktop/check3.xlsx'

# 读取Excel文件
df = pd.read_excel(excel_file)

# 筛选条件：只处理"业务"列不为2/5/99的投诉
if '业务' in df.columns:
    # 将业务列转换为字符串类型，确保比较正确
    df['业务'] = df['业务'].astype(str)
    # 创建筛选条件：业务列值不在 ['2','5','99'] 中
    filter_condition = ~df['业务'].isin(['2', '5'])
    # 应用筛选条件
    df = df[filter_condition]
    print(f"筛选后数据量: {len(df)} 条")
else:
    print("警告：数据文件中无'业务'列，将处理所有数据")

# 更新后的业务类型编码映射表（删除了02类别）
BUSINESS_TYPES = {
    "01": "网贷/现金贷业务",
    "03": "消费分期/消费贷款业务",  # 更新类别名称
    "04": "支付/扣费业务",
    "05": "催收业务",
    "99": "其他业务"
}

def classify_complaint(content):
    try:
        # 更新后的分类定义（明确包含车贷）
        category_definitions = (
            "业务类型定义及编码：\n"
            "01-网贷/现金贷业务：包括网络贷款、现金借贷、信用贷款等（不限用途）\n"
            "03-消费分期/消费贷款业务：商品或服务分期付款（非信用卡分期）以及明确用于消费用途的贷款（包括车贷、家电分期、教育分期等）\n"
            "04-支付/扣费业务：支付交易、资金盗刷、错误扣款等\n"
            "05-催收业务：催收行为、骚扰电话、威胁恐吓等\n"
            "99-其他业务：不属于以上类别的业务\n\n"
        )
        
        # 统一系统提示
        system_prompt = (
            "作为金融业务专家，请严格根据投诉内容判断投诉人涉及的核心业务性质分类：\n"
            f"{category_definitions}"
            "特别注意：\n"
            "1. 车贷属于消费贷款，应归类为03\n"
            "2. 明确用于消费用途的贷款应归类为03\n"
            "输出要求：\n"
            "1. 严格按JSON格式输出\n"
            "2. 选择最相关的一个业务类型编码\n"
            '3. 输出结构：{"label":"编码", "reason":"分类理由"}'
        )
        
        # 调用模型分类
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"投诉内容：{content}"}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        # 解析结果
        result = json.loads(response.choices[0].message.content.strip())
        label = result.get("label", "99")
        reason = result.get("reason", "")
        
        # 防止出现已删除的02类别
        if label == "02":
            label = "99"
            reason = "原分类为已删除的信用卡业务，调整为其他业务"
                
        return label, reason
    
    except Exception as e:
        return "99", f"处理失败: {str(e)}"

# 初始化列
df['业务编码_c3'] = ""
df['业务类型_c3'] = ""
df['分类理由_c3'] = ""

# 检查输出文件是否存在
if not os.path.exists(output_file):
    # 创建新Excel文件
    df.to_excel(output_file, index=False)
    processed_count = 0
else:
    # 读取已处理的数据
    try:
        processed_df = pd.read_excel(output_file)
        processed_count = len(processed_df)
        print(f"断点续传: 已处理 {processed_count} 条")
    except:
        # 如果读取失败，从头开始
        processed_count = 0
        print("输出文件读取失败，从头开始处理")

try:
    for idx in tqdm(range(processed_count, len(df)), desc="分类处理"):
        content = df.at[idx, "投诉内容"]
        
        # 调用分类函数
        code, reason = classify_complaint(content)
        
        # 写入DataFrame
        df.at[idx, '业务编码_c3'] = code
        df.at[idx, '业务类型_c3'] = BUSINESS_TYPES.get(code, "未知业务")
        df.at[idx, '分类理由_c3'] = reason
               
        # 定期保存（Excel格式）
        if (idx + 1) % 50 == 0 or idx == len(df) - 1:
            # 保存为Excel文件
            df.to_excel(output_file, index=False)
            print(f"已保存 {idx+1} 条记录")
except Exception as e:
    # 异常中断时保存进度
    df.to_excel(output_file, index=False)
    print(f"异常中断! 已保存进度: {output_file}")
    raise e

print("处理完成！")