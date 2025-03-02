# 人工智能词汇
# 人工智能 AI产品 AI芯片 机器翻译 机器学习
# 计算机视觉 人机交互 深度学习 神经网络 生物识别
# 图像识别 数据挖掘 特征识别 语音合成 语音识别
# 知识图谱 智慧银行 智能保险 人机协同 智能监管
# 智能教育 智能客服 智能零售 智能农业 智能投顾
# 增强现实 虚拟现实 智能医疗 智能音箱 智能语音
# 智能政务 自动驾驶 智能运输 卷积神经网络 声纹识别
# 特征提取 无人驾驶 智能家居 问答系统 人脸识别
# 商业智能 智慧金融 循环神经网络 强化学习 智能体
# 智能养老 大数据营销 大数据风控 大数据分析 大数据处理
# 支持向量机 SVM 长短期记忆 LSTM 机器人流程自动化 自然语言处理 分布式计算
# 知识表示 智能芯片 可穿戴产品 大数据管理 智能传感器
# 模式识别 边缘计算 大数据平台 智能计算 智能搜索
# 物联网 云计算 增强智能 语音交互 智能环保
# 人机对话 深度神经网络 大数据运营
import pandas as pd
import os
from tqdm import tqdm 


vulnerable_keywords = [
    '没文化', '没有学历', '没什么文化', '没有文化', '不识字', '不认字', '没读过书', '读书少', '小学文化', '初中文化',
    '小学毕业', '初中毕业', '不懂', '农民', '种地', '务农', '农村妇女', '农民工', '庄稼人', '农村人', '乡下人',
    '老人', '老年人', '年纪', '年龄大了', '年事已高', '年迈', '退休', '老人家', '高龄', '五十多岁', '六十多岁',
    '七十多岁', '八十多岁', '五六十岁', '六七十岁', '七八十岁', '五十岁', '六十岁', '七十岁', '八十岁', '50岁',
    '60岁', '70岁', '80岁', '6旬', '7旬', '8旬', '六旬', '七旬', '八旬', '爷爷', '奶奶', '姥姥', '姥爷', '外婆',
    '外公', '父亲', '母亲', '长辈', '老太太', '二老', '老实', '本分', '单亲家庭', '贫穷', '低保', '贫困户',
    '低保户', '困难户', '特困', '低收入', '收入微薄', '无业', '残疾', '体弱多病', '身体不好', '病人', '下岗',
    '失业'
]

# 统计包含关键词的投诉数量
def count_ai_complaints(file_path):
    df = pd.read_csv(file_path, usecols=['发起投诉内容', '发布时间'])
    ai_complaints = df[df['发起投诉内容'].str.contains('|'.join(vulnerable_keywords), case=False, na=False)]
    return len(ai_complaints), ai_complaints

# 统计64个CSV文件的总数量
def count_complaints_in_folder(folder_path):
    ai_complaints_total = 0
    ai_complaints_by_year = {}  # 按年份统计投诉数
    csv_files = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if filename.endswith('.csv') and not filename.startswith('.')]
    for filename in tqdm(csv_files, desc="Processing files", unit="file"):
        if filename.endswith('.csv') and not filename.startswith('.'):
            file_path = os.path.join(folder_path, filename)
            ai_complaints, df = count_ai_complaints(file_path)
            ai_complaints_total += ai_complaints
            
            # 提取年份信息：从'发布日'列提取年份
            df['year'] = pd.to_datetime(df['发布时间'], errors='coerce').dt.year
            for year in df['year'].dropna().unique():
                if year not in ai_complaints_by_year:
                    ai_complaints_by_year[year] = 0
                ai_complaints_by_year[year] += len(df[df['year'] == year])
    
    print(f"Total vulnerable-related complaints: {ai_complaints_total}")
    for year, count in ai_complaints_by_year.items():
        print(f"Year {year}: {count} vulnerable-related complaints")

# 指定包含CSV文件的文件夹路径
folder_path = '/Users/chenyaxin/Desktop/互联网旅游公约/原始数据处理'

# 统计投诉
count_complaints_in_folder(folder_path)