
from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import re
import json
import os
client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

# csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/classify_fin_processed.csv'
# output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/business_classify.csv'

# csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/business_classify.csv'
# output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/business_classify_dp.csv'

csv_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/business_classify_dp.csv'
output_file = '/Users/chenyaxin/Desktop/privacy/分类数据处理/business_classify_qw.csv'

df = pd.read_csv(csv_file)

# 业务类型编码映射表
BUSINESS_TYPES = {
    "01": "网贷/现金贷业务",
    "02": "信用卡业务",
    "03": "消费分期业务",
    "04": "支付/扣费业务",
    "05": "催收业务",
    "99": "其他业务"
}

# 根据业务类型分类
def classify_complaint(content):
    try:
        # 第一步：关键词初筛
        credit_card_keywords = ["信用卡", "贷记卡", "信用额度", "账单分期"]
        has_keyword = any(kw in content for kw in credit_card_keywords)
        
        # 第二步：构建分类系统提示（保留详细类别解释）
        category_definitions = (
            "业务类型定义及编码：\n"
            "01-网贷/现金贷业务：包括网络贷款、现金借贷、信用贷款等\n"
            "02-信用卡业务：信用卡申请、额度调整、年费、分期等核心业务\n"
            "03-消费分期业务：商品或服务分期付款（非信用卡分期）\n"
            "04-支付/扣费业务：支付交易、资金盗刷、错误扣款等\n"
            "05-催收业务：催收行为、骚扰电话、威胁恐吓等\n"
            "99-其他业务：不属于以上类别的业务\n\n"
        )
        
        # 根据是否含关键词定制系统提示
        if has_keyword:
            system_prompt = (
                "作为金融业务专家，请严格根据投诉内容判断投诉人涉及的核心业务性质分类：\n"
                f"{category_definitions}"
                "特别注意：\n"
                "1. 当投诉涉及信用卡催收行为时，应归类为05（催收业务）\n"
                "2. 当投诉涉及信用卡盗刷/错误扣款时，应归类为04（支付/扣费）\n"
                "3. 只有直接涉及信用卡核心功能（申请/额度/年费等）才归类为02\n"
                "4. 信用卡分期付款应归类为02（属于信用卡核心业务）\n"
                "输出要求：\n"
                "1. 严格按JSON格式输出\n"
                "2. 选择最相关的一个业务类型编码\n"
                '3. 输出结构：{"label":"编码", "reason":"分类理由"}'
            )
        else:
            system_prompt = (
                "作为金融业务专家，请根据投诉内容分析业务类型：\n"
                f"{category_definitions}"
                "输出要求：\n"
                "1. 严格按JSON格式输出\n"
                "2. 选择最相关的一个业务类型编码\n"
                '3. 输出结构：{"label":"编码", "reason":"分类理由"}'
            )
        
        # 调用模型分类
        response = client.chat.completions.create(
            model="Qwen/Qwen3-32B",   
            # Qwen/Qwen3-8B
            # Pro/deepseek-ai/DeepSeek-V3
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
        
        # 信用卡关键词特殊处理
        if has_keyword:
            if label == "02":
                return "02", f"信用卡核心业务：" + reason
            else:
                return label, f"含信用卡关键词但实际属于{label}类：" + reason
                
        return label, reason
    
    except Exception as e:
        return "99", f"处理失败: {str(e)}"
    
# df['业务编码'] = ""
# df['业务类型'] = ""
# df['分类理由'] = ""

df['业务编码_dp'] = ""
df['业务类型_dp'] = ""
df['分类理由_dp'] = ""
if not os.path.exists(output_file):
    # 首次运行：创建新文件并写表头
    df.to_csv(output_file, index=False)
    processed_count = 0
else:
    # 断点续传：读取已处理行数
    processed_df = pd.read_csv(output_file)
    processed_count = len(processed_df)
    print(f"断点续传: 已处理 {processed_count} 条")

try:
    for idx in tqdm(range(processed_count, len(df)), desc="分类处理"):
        content = df.at[idx, "投诉内容"]
        
        # 调用分类函数
        code, reason = classify_complaint(content)
        
        # 写入DataFrame
        # df.at[idx, '业务编码'] = code
        # df.at[idx, '业务类型'] = BUSINESS_TYPES.get(code, "未知业务")
        # df.at[idx, '分类理由'] = reason

        df.at[idx, '业务编码_dp'] = code
        df.at[idx, '业务类型_dp'] = BUSINESS_TYPES.get(code, "未知业务")
        df.at[idx, '分类理由_dp'] = reason
               
        # 修改点5：每50条实时保存（覆盖原文件）
        if (idx + 1) % 50 == 0 or idx == len(df) - 1:
            df.to_csv(output_file, index=False)
            print(f"已保存 {idx+1} 条记录")
except Exception as e:
    df.to_csv(output_file, index=False)
    print(f"异常中断! 已保存进度: {output_file}")
    raise e

print("处理完成！")


