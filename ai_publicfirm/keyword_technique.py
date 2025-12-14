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

def filter_data_analysis_jobs(csv_file, job_desc_column):
    """
    筛选包含数据分析关键词的职位
    
    参数:
    csv_file: CSV文件路径
    job_desc_column: 职位描述列名
    
    返回:
    筛选后的DataFrame
    """
    # 读取CSV文件
    df = pd.read_csv(csv_file)
    
    # 检查必要的列是否存在
    required_columns = [job_desc_column, '招聘发布年份', '来源', '企业名称']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"CSV文件中缺少必要的列: {col}")
    
    # 筛选包含关键词的职位
    def contains_keyword(text):
        if pd.isna(text):
            return False
        text = str(text)
        return any(keyword in text for keyword in data_analysis_keywords)
    
    mask = df[job_desc_column].apply(contains_keyword)
    filtered_df = df[mask].copy()
    
    print(f"原始数据行数: {len(df)}")
    print(f"筛选后数据行数: {len(filtered_df)}")
    
    return filtered_df

def remove_duplicate_rows(df):
    """
    去除所有列内容都完全重复的行
    
    参数:
    df: DataFrame
    
    返回:
    去重后的DataFrame
    """
    # 去除所有列内容都完全重复的行
    df_no_duplicates = df.drop_duplicates(keep='first')
    
    print(f"去重前行数: {len(df)}")
    print(f"去重后行数: {len(df_no_duplicates)}")
    print(f"删除了 {len(df) - len(df_no_duplicates)} 条完全重复的记录")
    
    return df_no_duplicates

def main():
    # 文件路径和列名配置
    csv_file_path = '/Users/chenyaxin/Desktop/上市公司投诉数据探究/招聘数据处理/上市公司招聘大数据/上市公司招聘大数据2014-2023年.csv'  # 替换为你的CSV文件路径
    job_description_column = "职位描述"  # 替换为您的职位描述列名
    
    try:
        # 步骤1: 筛选数据分析相关职位
        print("正在筛选数据分析相关职位...")
        filtered_jobs = filter_data_analysis_jobs(csv_file_path, job_description_column)
        
        # 步骤2: 去除所有列内容完全重复的行
        print("正在去除完全重复的行...")
        unique_jobs = remove_duplicate_rows(filtered_jobs)
        
        # 保存结果（包含所有筛选出的数据，不进行抽样）
        output_file = "/Users/chenyaxin/Desktop/AI数据职位_全部.csv"
        unique_jobs.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"结果已保存到: {output_file}")
        
        # 打印统计信息
        print("\n最终统计信息:")
        print(f"总记录数: {len(unique_jobs)}")
        print("按年份分布:")
        print(unique_jobs['招聘发布年份'].value_counts().sort_index())
        print("\n按来源分布:")
        print(unique_jobs['来源'].value_counts())
        print("\n按企业分布 (前20名):")
        print(unique_jobs['企业名称'].value_counts().head(20))
        
        # 关键词统计
        keyword_counts = defaultdict(int)
        for text in unique_jobs[job_description_column]:
            if pd.isna(text):
                continue
            text_str = str(text)
            for keyword in data_analysis_keywords:
                if keyword in text_str:
                    keyword_counts[keyword] += 1
        
        print("\n关键词出现频率统计 (前20名):")
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"  {keyword}: {count}次")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main()