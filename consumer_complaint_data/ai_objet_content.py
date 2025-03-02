import pandas as pd
import os
from tqdm import tqdm

# 定义人工智能相关的关键词（之前提供的词汇列表）
ai_keywords = [
    '人工智能', 'AI产品', 'AI芯片', '机器翻译', '机器学习', '计算机视觉', '人机交互', '深度学习', '神经网络', 
    '生物识别', '图像识别', '数据挖掘', '特征识别', '语音合成', '语音识别', '知识图谱', '智慧银行', '智能保险',
    '人机协同', '智能监管', '智能教育', '智能客服', '智能零售', '智能农业', '智能投顾', '增强现实', '虚拟现实',
    '智能医疗', '智能音箱', '智能语音', '智能政务', '自动驾驶', '智能运输', '卷积神经网络', '声纹识别', '特征提取',
    '无人驾驶', '智能家居', '问答系统', '人脸识别', '商业智能', '智慧金融', '循环神经网络', '强化学习', '智能体',
    '智能养老', '大数据营销', '大数据风控', '大数据分析', '大数据处理', '支持向量机', 'SVM', '长短期记忆', 'LSTM',
    '机器人流程自动化', '自然语言处理', '分布式计算', '知识表示', '智能芯片', '可穿戴产品', '大数据管理', '智能传感器',
    '模式识别', '边缘计算', '大数据平台', '智能计算', '智能搜索', '物联网', '云计算', '增强智能', '语音交互', '智能环保',
    '人机对话', '深度神经网络', '大数据运营'
]

# 统计包含关键词的投诉内容，并按投诉对象分类
def count_ai_complaints_by_object(file_path):
    # 读取CSV文件
    df = pd.read_csv(file_path, usecols=['发起投诉内容', '投诉对象', '发布时间'])
    
    # 筛选包含人工智能相关关键词的投诉
    ai_complaints = df[df['发起投诉内容'].str.contains('|'.join(ai_keywords), case=False, na=False)]
    if ai_complaints.empty:
        return pd.DataFrame(columns=['投诉对象', 'ai_complaint_count', 'total_complaint_count']), pd.DataFrame(columns=['投诉对象', '发布时间', '发起投诉内容'])
    ai_complaint_objects = ai_complaints['投诉对象'].unique()
    
    total_complaints_by_object = df[df['投诉对象'].isin(ai_complaint_objects)].groupby('投诉对象').agg(
        total_complaint_count=('发起投诉内容', 'size')
    ).reset_index()

    # 统计每个投诉对象的人工智能投诉数量
    ai_complaints_by_object = ai_complaints.groupby('投诉对象').agg(
        ai_complaint_count=('发起投诉内容', 'size')
    ).reset_index()

    result = pd.merge(ai_complaints_by_object, total_complaints_by_object, on='投诉对象', how='left')
    return result, ai_complaints

# 统计64个CSV文件的总数量，并按投诉对象统计人工智能相关投诉
def count_complaints_in_folder_by_object(folder_path, output_csv_1, output_csv_2):
    all_complaints = pd.DataFrame(columns=['投诉对象', '投诉时间', '发起投诉内容'])
    all_results = pd.DataFrame(columns=['投诉对象', 'ai_complaint_count', 'total_complaint_count'])
   
    csv_files = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if filename.endswith('.csv') and not filename.startswith('.')]
    for filename in tqdm(csv_files, desc="Processing files", unit="file"):
        result, ai_complaints = count_ai_complaints_by_object(filename)
        # 将人工智能相关的投诉内容保留到表格1
        all_complaints = pd.concat([all_complaints, ai_complaints[['投诉对象', '发布时间', '发起投诉内容']]], ignore_index=True)
        all_results = pd.concat([all_results, result], ignore_index=True)
        
    # 合并所有文件的统计数据
    # 对人工智能投诉数量进行加总
    final_result = all_results.groupby('投诉对象').agg(
        ai_complaint_count=('ai_complaint_count', 'sum'),
        total_complaint_count=('total_complaint_count', 'sum')
    ).reset_index()
    
    # 输出到CSV文件
    all_complaints.to_csv(output_csv_1, index=False)
    print(f"Data saved to {output_csv_1}")
    
    final_result.to_csv(output_csv_2, index=False)
    print(f"Data saved to {output_csv_2}")
    
# 指定包含CSV文件的文件夹路径
folder_path = '/Users/chenyaxin/Desktop/互联网旅游公约/原始数据处理'
output_csv_1 = '/Users/chenyaxin/Desktop/ai_complaints.csv'
output_csv_2 = '/Users/chenyaxin/Desktop/ai_complaints_summary.csv'
# 统计投诉并保存结果
count_complaints_in_folder_by_object(folder_path, output_csv_1, output_csv_2)
