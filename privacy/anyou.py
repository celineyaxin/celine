import pandas as pd
import json
from openai import OpenAI
import time

# 初始化 OpenAI 客户端
client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", 
                base_url="https://api.siliconflow.cn/v1")

# 分类标准
classification_criteria = """
你是一个法律案由分类专家。请严格按以下规则分析案由：
    1. 输出必须是JSON格式：{"是否相关":"是/否","关联强度":"高/中/低/无","关联场景":"关键词短语","风险标记":"⚠️/✅/空"}
    2. 判定逻辑：
       - 直接相关(高)：案由含"隐私""个人信息""数据""网络侵权"等关键词
       - 间接相关(中)：涉及用户数据的服务/合同纠纷(金融/医疗/电商/劳动)
       - 潜在相关(低)：可能涉及个人信息的场景(如融资租赁/委托合同)
       - 不相关：无数据交互场景(如票据/纯物权纠纷)
    3. 关联场景：用3-5个关键词描述，用|分隔
    4. 风险标记：
       - 高关联强度 ➔ "⚠️"
       - 含"确认合同无效""合规"等 ➔ "✅"
       - 否则留空
    5. 示例：
       输入: "网络侵权责任纠纷" → 输出: {"是否相关":"是","关联强度":"高","关联场景":"隐私泄露|违规收集","风险标记":"⚠️"}
       输入: "票据追索权纠纷" → 输出: {"是否相关":"否","关联强度":"无","关联场景":"","风险标记":""}
"""

# 读取 Excel 文件
def read_excel(file_path):
    df = pd.read_excel(file_path)
    return df

# 调用 API 判断案由是否与个人信息保护法相关
def classify_complaint(content):
    try:
        response = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": classification_criteria
                },
                {
                    "role": "user",
                    "content": f"案由：{content}"
                }
            ],
            stream=False
        )
        # 获取完整的响应内容
        full_response = response.choices[0].message.content.strip()
        
        # 尝试解析JSON
        try:
            return json.loads(full_response)
        except json.JSONDecodeError:
            # 如果解析失败，返回错误信息
            return {
                "是否相关": "解析错误",
                "关联强度": "",
                "关联场景": "",
                "风险标记": "",
                "原始响应": full_response
            }
            
    except Exception as e:
        return {
            "是否相关": "API错误",
            "关联强度": "",
            "关联场景": "",
            "风险标记": "",
            "错误信息": str(e)
        }

# 主函数
def main():
    # 读取 Excel 文件
    file_path = "/Users/chenyaxin/Desktop/案由.xlsx"  # 替换为你的 Excel 文件路径
    df = read_excel(file_path)
    
    # 添加进度条
    from tqdm import tqdm
    tqdm.pandas(desc="处理案由")
    
    # 处理每个案由并解析结果
    results = []
    for _, row in tqdm(df.iterrows(), total=len(df)):
        content = row["案由"]
        result = classify_complaint(content)
        
        # 添加0.5秒延迟避免请求过快
        time.sleep(0.5)
        
        # 合并原始数据和分类结果
        merged = {**row.to_dict(), **result}
        results.append(merged)
    
    # 创建新的DataFrame
    result_df = pd.DataFrame(results)
    
    # 保存结果到新的 Excel 文件
    output_file = "/Users/chenyaxin/Desktop/案由——2.xlsx"
    result_df.to_excel(output_file, index=False)
    print(f"结果已保存到 {output_file}")
    
    # 显示相关性统计
    print("\n相关性统计:")
    print(result_df["是否相关"].value_counts())

if __name__ == "__main__":
    main()