import pandas as pd
import numpy as np
from collections import defaultdict

# 数据分析相关关键词（更新为AI和数据相关关键词）
data_analysis_keywords = [
    "机器学习", "深度学习", "自然语言处理", "图像识别", "数据挖掘",
    "预测模型", "神经网络", "AI聊天机器人", "监督学习", "无监督学习",
    "文本挖掘", "情感分析", "机器翻译", "计算机视觉", "模式识别",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas",
    "数据清洗", "数据转换", "数据聚合", "决策树", "随机森林",
    "支持向量机", "SVM", "逻辑回归", "线性回归", "卷积神经网络",
    "CNN", "循环神经网络", "RNN", "长短期记忆网络", "LSTM",
    "Transformer", "词嵌入", "词性标注", "命名实体识别", "数据隐私",
    "数据安全", "合规性", "法律框架", "项目规划", "风险管理", "项目监控",
    "数据录入", "数据存储", "数据分析", "数据管理", "数据加密",
    "数据预处理", "数据质量评估", "数据科学", "数据建模", "数据治理",
    "数据保护", "数据平台服务", "数据库管理", "数据仓库设计", "数据湖管理",
    "数据可视化", "商业智能工具", "数据驱动决策", "数据合规性", "数据隐私法规",
    "数据架构设计", "数据流程优化", "数据质量控制", "数据备份与恢复", "云存储",
    "数据湖架构", "数据仓库架构", "数据库设计", "数据库优化", "数据库性能监控",
    "数据库安全", "访问控制", "安全审计", "数据一致性", "Tableau",
    "Power BI", "D3.js", "Matplotlib", "Seaborn"
]

def add_keyword_analysis_columns(df, job_desc_column):
    """
    在原始数据中添加关键词分析列
    
    参数:
    df: DataFrame
    job_desc_column: 职位描述列名
    
    返回:
    添加了分析列的DataFrame
    """
    # 创建新列
    df['是否包含关键词'] = 0
    df['包含关键词数量'] = 0
    df['包含的具体关键词'] = ''
    
    print("正在分析关键词...")
    
    for idx, row in df.iterrows():
        text = row[job_desc_column]
        
        if pd.isna(text) or str(text).strip() == '':
            continue
            
        text_str = str(text)
        found_keywords = []
        
        # 检查每个关键词
        for keyword in data_analysis_keywords:
            if keyword in text_str:
                found_keywords.append(keyword)
        
        # 更新列
        if found_keywords:
            df.at[idx, '是否包含关键词'] = 1
            df.at[idx, '包含关键词数量'] = len(found_keywords)
            df.at[idx, '包含的具体关键词'] = '、'.join(found_keywords)
    
    # 统计信息
    total_with_keywords = df['是否包含关键词'].sum()
    print(f"包含关键词的记录数: {total_with_keywords}")
    print(f"关键词覆盖率: {total_with_keywords/len(df)*100:.2f}%")
    
    # 关键词频率统计
    keyword_freq = defaultdict(int)
    for keywords_str in df['包含的具体关键词']:
        if keywords_str:
            for keyword in keywords_str.split('、'):
                keyword_freq[keyword] += 1
    
    print("\n关键词出现频率统计 (前20名):")
    for keyword, count in sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {keyword}: {count}次")
    
    return df

def remove_duplicate_rows(df):
    """
    去除所有列内容都完全重复的行
    
    参数:
    df: DataFrame
    
    返回:
    去重后的DataFrame
    """
    # 去除所有列内容都完全重复的行
    original_count = len(df)
    df_no_duplicates = df.drop_duplicates(keep='first')
    
    print(f"去重前行数: {original_count}")
    print(f"去重后行数: {len(df_no_duplicates)}")
    print(f"删除了 {original_count - len(df_no_duplicates)} 条完全重复的记录")
    
    return df_no_duplicates

def main():
    # 文件路径和列名配置
    csv_file_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/招聘数据处理/上市公司招聘大数据/上市公司招聘大数据2014-2023年.csv'  # 替换为你的CSV文件路径
    job_description_column = "职位描述"  # 替换为您的职位描述列名
    
    try:
        # 读取原始数据
        print("正在读取原始数据...")
        df = pd.read_csv(csv_file_path)
        print(f"原始数据行数: {len(df)}")
        
        # 步骤1: 添加关键词分析列
        print("正在添加关键词分析列...")
        df_with_keywords = add_keyword_analysis_columns(df, job_description_column)
        
        # 步骤2: 去除所有列内容完全重复的行
        print("正在去除完全重复的行...")
        final_df = remove_duplicate_rows(df_with_keywords)
        
        # 保存结果
        output_file = "/Users/chenyaxin/Desktop/上市公司招聘数据_关键词分析.csv"
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"结果已保存到: {output_file}")
        
        # 打印最终统计信息
        print("\n=== 最终统计信息 ===")
        print(f"总记录数: {len(final_df)}")
        print(f"包含关键词的记录数: {final_df['是否包含关键词'].sum()}")
        print(f"关键词覆盖率: {final_df['是否包含关键词'].sum()/len(final_df)*100:.2f}%")
        
        # 按年份统计
        print("\n按年份分布 (包含关键词的记录):")
        year_stats = final_df[final_df['是否包含关键词'] == 1].groupby('招聘发布年份').size()
        print(year_stats)
        
        # 按来源统计
        print("\n按来源分布 (包含关键词的记录):")
        source_stats = final_df[final_df['是否包含关键词'] == 1].groupby('来源').size()
        print(source_stats)
        
        # 关键词数量分布
        print("\n关键词数量分布:")
        keyword_count_stats = final_df[final_df['是否包含关键词'] == 1]['包含关键词数量'].value_counts().sort_index()
        for count, freq in keyword_count_stats.items():
            print(f"  包含{count}个关键词: {freq}条记录")
        
        # 最常出现的关键词企业
        print("\n包含关键词最多的企业 (前10名):")
        company_keyword_stats = final_df[final_df['是否包含关键词'] == 1]['企业名称'].value_counts().head(10)
        print(company_keyword_stats)
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()