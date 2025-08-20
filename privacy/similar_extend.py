from openai import OpenAI
import pandas as pd
from tqdm import tqdm 
import os

# 初始化OpenAI客户端
client = OpenAI(api_key="sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc", 
                base_url="https://api.siliconflow.cn/v1")

# 文件路径
csv_file = '/Users/chenyaxin/Desktop/类别1.csv'
output_file = '/Users/chenyaxin/Desktop/similar2.csv'

# 读取CSV文件
df = pd.read_csv(csv_file)

# 批处理大小 - 每处理多少条原始行写入一次文件
BATCH_SIZE = 10  # 可以根据需要调整

def generate_similar_expressions(content, num_samples=3):
    """生成相似表达的函数"""
    try:
        # 优化提示词
        system_prompt = (
            "你是文本生成专家。请为以下投诉内容生成{num}条语义相似但表达不同的文本（限中文）：\n\n"
            "要求：\n"
            "1. 保留原始语义核心\n"
            "2. 使用不同的词汇和句式\n"
            "3. 每条生成文本单独一行\n"
            "4. 不要包含编号或额外说明\n"
            "5. 保持自然流畅\n\n"
            "上下文：与'诱导贷款'或'诱导贷前消费'相关的投诉内容\n"
        ).format(num=num_samples)
        
        # 调用API生成相似文本
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-V3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"原始投诉内容：{content}"}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # 处理API响应
        generated_text = response.choices[0].message.content.strip()
        
        # 按行分割并清理结果
        similar_texts = [text.strip() for text in generated_text.split('\n') if text.strip()]
        
        # 确保返回指定数量的结果
        return similar_texts[:num_samples]
    
    except Exception as e:
        print(f"生成相似表达时出错: {e}")
        # 返回占位文本以便调试
        return [f"生成错误: {e}"] * num_samples

# 存储增强后的数据
augmented_rows = []

# 检查输出文件是否存在，如果存在则删除
if os.path.exists(output_file):
    os.remove(output_file)
    print(f"已删除旧文件: {output_file}")

# 创建新文件并写入表头

header = pd.DataFrame(columns=['原始投诉内容', '模型生成内容'])
header.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"已创建新文件并写入表头: {output_file}")

# 处理所有数据
total_rows = len(df)
processed_count = 0
batch_count = 0

print(f"开始处理 {total_rows} 条数据...")
print(f"批处理大小: {BATCH_SIZE} 条原始行")

for index, row in tqdm(df.iterrows(), total=total_rows, desc="生成相似表达"):
    original_complaint = row['投诉内容']
    
    # 生成相似表达
    similar_texts = generate_similar_expressions(original_complaint, 3)
    
    # 为每个相似表达创建新行
    for similar_text in similar_texts:
        # 只保留两列：原始内容和生成内容
        new_row = {
            '原始投诉内容': original_complaint,
            '模型生成内容': similar_text
        }
        augmented_rows.append(new_row)
        
    processed_count += 1
    
    # 每处理BATCH_SIZE条原始行后写入文件
    if processed_count % BATCH_SIZE == 0:
        batch_count += 1
        batch_df = pd.DataFrame(augmented_rows)
        
        # 追加写入CSV文件
        batch_df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        
        # 计算进度
        progress_percent = (processed_count / total_rows) * 100
        print(f"\n已处理 {processed_count}/{total_rows} 条原始行 ({progress_percent:.1f}%)")
        print(f"写入批次 #{batch_count}: 添加 {len(batch_df)} 行生成数据")
        
        # 清空临时存储
        augmented_rows = []

# 写入剩余的数据
if augmented_rows:
    batch_count += 1
    batch_df = pd.DataFrame(augmented_rows)
    batch_df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8-sig')
    print(f"\n写入最后批次 #{batch_count}: 添加 {len(batch_df)} 行生成数据")

# 最终统计
final_df = pd.read_csv(output_file)
print(f"\n处理完成!")
print(f"原始数据行数: {total_rows}")
print(f"生成数据总行数: {len(final_df)}")
print(f"结果已保存至: {output_file}")