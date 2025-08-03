from openai import OpenAI
import pandas as pd
from tqdm import tqdm
import re

# 初始化 OpenAI 客户端
client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", base_url="https://api.siliconflow.cn/v1")

# 输入和输出文件路径
excel_file = '/Users/chenyaxin/Desktop/supplement_fraud_sample_3000.xlsx'
output_file = '/Users/chenyaxin/Desktop/add_sample.xlsx'
# 读取 CSV 文件
df = pd.read_excel(excel_file)

# 定义分类标准和问题
classification_criteria = """
您是一个专业的金融投诉分类助手，请严格按照用户要求进行分类。需要给出类别的序号，并给出你判断的理由（精简）。
请注意在分类过程中尽量不要出现交叉多个分类，以投诉内容中最主要的欺诈类型所属类别为主：
[分类标准]
1. 不依赖个人信息的欺诈
   11-诱导消费：通过话术诱导消费，不涉及个人信息（套路）
   12-虚假服务：
        121-充值会员欺诈：承诺充值会员可获服务但未兑现
        122-虚假放贷：承诺放贷但未履行
        123-提前交费欺诈：要求提前支付各种费用
   13-冒充平台：冒充正规平台进行诈骗
   14-还款障碍：人为设置还款障碍制造逾期

2. 依赖个人信息的欺诈
   21-强制搭售：强制捆绑销售保险/会员等
   22-强制下款：未经同意强制下款
   23-自动划扣：未经授权自动扣款
   24-精准推荐：基于个人信息的精准推销

3. 费用及利率争议
   31-高利贷：利率超过法定标准
   32-隐藏费用：未明确告知的额外费用

0. 非欺诈投诉
   01-服务问题：客服、服务态度等问题
   02-技术故障：系统错误、技术问题
   03-其他：明显不属于欺诈的投诉
"""

# 分类函数
def classify_complaint(content):
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen3-32B",
            messages=[
                {
                    "role": "system",
                    "content": classification_criteria
                },
                {
                    "role": "user",
                    "content": f"投诉内容：{content}"
                }
            ],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"异常：{e}"
    

def split_model_output(output):
    if not isinstance(output, str):
        output = str(output)
    output = output.strip()
    
    # 初始化结果字典
    result = {
        "one_digit": [],    # 一位数分类编号 (0-9)
        "two_digit": [],    # 两位数分类编号 (10-99)
        "three_digit": [],  # 三位数分类编号 (100-999)
        "reason": ""        # 判断理由
    }
    
    # 处理带**标记的结构化输出
    if "**分类序号：" in output:
        # 提取分类部分
        category_match = re.search(r'\*\*分类序号：\*\*([\s\S]*?)(?:\*\*理由：\*\*|$)', output)
        if category_match:
            category_text = category_match.group(1).strip()
            
            # 提取所有分类编号
            all_nums = re.findall(r'\b(\d{1,3})\b', category_text)
            
            # 按位数分类
            for num in all_nums:
                if len(num) == 1:
                    result["one_digit"].append(num)
                elif len(num) == 2:
                    result["two_digit"].append(num)
                elif len(num) == 3:
                    result["three_digit"].append(num)
            
            # 提取理由部分
            reason_start = category_match.end()
            reason = output[reason_start:].strip()
            reason = re.sub(r'^\*\*理由：\*\*', '', reason).strip()
            result["reason"] = reason
            
            return result
    
    # 处理传统格式
    header_match = re.match(r'^(?:分类|类别|分类序号)[：:\s]*([\d\s，、,-]+)', output, re.IGNORECASE)
    if header_match:
        header = header_match.group(1)
        # 从头部提取所有分类编号
        all_nums = re.findall(r'\d{1,3}', header)
        
        # 按位数分类
        for num in all_nums:
            if len(num) == 1:
                result["one_digit"].append(num)
            elif len(num) == 2:
                result["two_digit"].append(num)
            elif len(num) == 3:
                result["three_digit"].append(num)
        
        # 获取理由部分
        reason = output[len(header_match.group(0)):].strip()
        reason = re.sub(r'^[：:，、\s-]+', '', reason)
        result["reason"] = reason
        
        return result
    
    # 兜底方案：在整个文本中搜索分类编号
    all_matches = re.findall(r'\b(\d{1,3})\b', output)
    for num in all_matches:
        if len(num) == 1:
            result["one_digit"].append(num)
        elif len(num) == 2:
            result["two_digit"].append(num)
        elif len(num) == 3:
            result["three_digit"].append(num)
    
    result["reason"] = output
    
    return result

# 根据两位数分类推导一位数分类
def derive_one_digit_from_two_digit(two_digit_list):
    one_digit_map = {
        '11': '1', '12': '1', '13': '1', '14': '1',
        '21': '2', '22': '2', '23': '2', '24': '2',
        '31': '3', '32': '3',
        '01': '0', '02': '0', '03': '0'
    }
    one_digit_set = set()
    for two_digit in two_digit_list:
        if two_digit in one_digit_map:
            one_digit_set.add(one_digit_map[two_digit])
    return list(one_digit_set)

# 设置分块大小
chunk_size = 50  # 每 50 条写入一次

# 遍历数据并分类
for start in tqdm(range(0, len(df), chunk_size), desc="Processing"):
    end = start + chunk_size
    chunk = df.iloc[start:end].copy()
    for idx in range(start, min(end, len(df))):
        content = df.at[idx, "投诉内容"]
        output = classify_complaint(content)
        result = split_model_output(output)

        # 将结果写入 DataFrame
        df.at[idx, "模型输出类别区分"] = output
        df.at[idx, "一位数分类"] = ",".join(result["one_digit"])
        df.at[idx, "两位数分类"] = ",".join(result["two_digit"])
        df.at[idx, "三位数分类"] = ",".join(result["three_digit"])
        df.at[idx, "分类理由"] = result["reason"]
        derived_one_digit = derive_one_digit_from_two_digit(result["two_digit"])
        df.at[idx, "推导一位数分类"] = ",".join(derived_one_digit)
    df.to_excel(output_file, index=False)

print(f"结果已保存到 {output_file}")
     