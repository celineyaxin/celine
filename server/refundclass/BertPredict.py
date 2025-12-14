import pandas as pd
from BertTrain import NewsClassifier
import torch
import os
from tqdm import tqdm

if __name__ == "__main__":
    data_paths = {
        'train': './train.csv',
        'dev': './dev.csv',
        'test': './test.csv',
        'financial_complains': './refund.csv'
    }
    if torch.cuda.is_available():
        print("GPU is available!")
        device = torch.device("cuda")
    else:
        print("GPU is not available. Using CPU instead.")
        device = torch.device("cpu")

    news_classifier = NewsClassifier(data_paths=data_paths, label_path='./class.txt', model_path='./chinese_L-12_H-768_A-12', save_path='./model')
    # 加载模型权重
    model_weights_path = os.path.join(news_classifier.save_path, 'best_model.pt')
    if os.path.exists(model_weights_path):
        news_classifier.model.load_state_dict(torch.load(model_weights_path, weights_only=True))
    
    # 读取CSV文件
    csv_path = data_paths['financial_complains'] 
    df = pd.read_csv(csv_path)

    # 显式添加预测列
    df['prediction'] = pd.Series(dtype=object)

    # 确保CSV中有text列
    if '发起投诉内容' not in df.columns:
        raise ValueError("CSV file does not contain a '发起投诉内容' column")

    df["发起投诉内容"] = df["发起投诉内容"].astype(object)
    for idx, row in tqdm(df.iterrows(), total=len(df), desc='Predicting'):
        text = row['发起投诉内容']
        if pd.isna(text) or text == '':
            continue
        df.at[idx, 'prediction'] = news_classifier.predict(text)

    output_csv_path = os.path.join(
        news_classifier.save_path,
        'financial_predictions_all.csv'
    )
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"Done! Saved to {output_csv_path}")