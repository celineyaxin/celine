import pandas as pd
from BertConsumer import NewsClassifier
import torch
import os
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from multiprocessing import Pool, Value, current_process

if __name__ == "__main__":
    data_paths = {
        'train': './Data/consumer_protection/train.csv',
        'dev': './Data/consumer_protection/dev.csv',
        'test': './Data/consumer_protection/test.csv',
        'test_five': './Data/consumer_protection/test_5.csv',
        'financial_complains': './Data/consumer_protection/financial_complains.csv'
    }
    news_classifier = NewsClassifier(data_paths = data_paths, label_path = './Data/consumer_protection/class.txt', model_path = './models/chinese_L-12_H-768_A-12', save_path = './Data/consumer_protection/')
    # 加载模型权重
    model_weights_path = os.path.join(news_classifier.save_path, 'best_model.pt')
    if os.path.exists(model_weights_path):
        news_classifier.model.load_state_dict(torch.load(model_weights_path))
    
    # 读取CSV文件
    csv_path = data_paths['financial_complains'] 
    # csv_path = data_paths['test_five'] 
    df = pd.read_csv(csv_path)

    # 显式添加预测列
    df['prediction'] = pd.Series(dtype=object)

    # 确保CSV中有text列
    if '投诉内容' not in df.columns:
        raise ValueError("CSV file does not contain a '投诉内容' column")

    # df['prediction'] = df['投诉内容'].apply(lambda x: news_classifier.predict(x))
    df["投诉内容"] = df["投诉内容"].astype(object)
    
    df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y年%m月%d日 %H:%M')

    # 设置要筛选的日期和时间范围
    start_date = '2020-09-01 00:00'
    end_date = '2021-01-31 23:59'

    # 使用布尔索引筛选出特定日期和时间范围内的行
    limited_df = df[(df['发布时间'] >= pd.to_datetime(start_date)) & (df['发布时间'] <= pd.to_datetime(end_date))]
    # limited_df = df
    print(limited_df)

    # 保存带有预测结果的新CSV文件
    # 将开始和结束日期格式化为字符串，格式例如：'20210201_1530'
    start_date_str = pd.to_datetime(start_date).strftime('%Y%m%d_%H%M')
    end_date_str = pd.to_datetime(end_date).strftime('%Y%m%d_%H%M')

    for index, row in tqdm(limited_df.iterrows(), total=limited_df.shape[0], desc='Processing'):
        if pd.isna(row['投诉内容']) or row['投诉内容'] == '':
            print(row)
            continue  # 跳过空行
        # 应用你的预测函数到每一行的 '投诉内容' 列
        limited_df.at[index, 'prediction'] = news_classifier.predict(row['投诉内容'])

    # 构造带有日期范围的输出CSV文件名
    output_csv_path = os.path.join(news_classifier.save_path, f'financial_predictions_{start_date_str}_{end_date_str}.csv')
    # output_csv_path = os.path.join(news_classifier.save_path, 'financial_test_5.csv')
    limited_df.to_csv(output_csv_path, index=False)
    print(f"Predictions saved to {output_csv_path}")