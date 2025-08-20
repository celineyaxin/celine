import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel
import pandas as pd
import numpy as np
import os
from tqdm import tqdm

class NewsClassifier:
    def __init__(self, data_paths, label_path, model_path, save_path, seed=1999):
        self.data_paths = data_paths
        self.label_path = label_path
        self.model_path = model_path
        self.save_path = save_path
        self.seed = seed
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.tokenizer = BertTokenizer.from_pretrained(self.model_path)
        self.labels = self._load_labels()
        self.model = None
        self.criterion = None
        self.optimizer = None
        self.train_dataset = None
        self.dev_dataset = None

        self.setup_seed()
        self.model = BertClassifier(self.labels, self.model_path).to(self.device)

        train_df = self.load_data(self.data_paths['train'])
        dev_df = self.load_data(self.data_paths['dev'])
        self.train_dataset = self.create_dataset(train_df)
        self.dev_dataset = self.create_dataset(dev_df)

    def _load_labels(self):
        with open(self.label_path, 'r') as f:
            return [row.strip() for row in f.readlines()]

    def setup_seed(self):
        torch.manual_seed(self.seed)
        torch.cuda.manual_seed_all(self.seed)
        np.random.seed(self.seed)
        torch.backends.cudnn.deterministic = True

    def load_data(self, path, limit=None):
        df = pd.read_csv(path, header=None)
        if limit:
            df = df.head(limit)
        df.columns = ['text', 'label']
        df.dropna(how='all', inplace=True)
        df = df.dropna(subset=["label"])
        df["text"] = df["text"].astype(object)
        df["label"] = df["label"].astype('int64')
        return df

    def create_dataset(self, df):
        texts = [self.tokenizer(text, padding='max_length', max_length=512, truncation=True, return_tensors="pt") for text in df["text"]]
        labels = df['label'].values
        return MyDataset(texts, labels)

    def get_misclassified_samples(self, df):
        self.model.eval()
        dataset = self.create_dataset(df)
        data_loader = DataLoader(dataset, batch_size=32)
        misclassified_samples = []

        with torch.no_grad():
            for inputs, labels in data_loader:
                input_ids = inputs['input_ids'].squeeze(1).to(self.device)
                attention_mask = inputs['attention_mask'].to(self.device)
                labels = labels.to(self.device)
                outputs = self.model(input_ids, attention_mask)
                _, predicted = torch.max(outputs, 1)
                misclassified_indices = (predicted != labels).nonzero(as_tuple=True)[0]
                for idx in misclassified_indices:
                    idx = idx.item()
                    misclassified_samples.append({
                        'text': df.iloc[idx]['text'],
                        'true_label': df.iloc[idx]['label'],
                        'predicted_label': predicted[idx].item()
                    })
        
        return misclassified_samples

class MyDataset(Dataset):
    def __init__(self, texts, labels):
        self.texts = texts
        self.labels = labels

    def __getitem__(self, idx):
        return self.texts[idx], self.labels[idx]

    def __len__(self):
        return len(self.labels)

class BertClassifier(nn.Module):
    def __init__(self, labels, model_path):
        super(BertClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(model_path)
        self.dropout = nn.Dropout(0.5)
        self.linear = nn.Linear(self.bert.config.hidden_size, len(labels))
        self.relu = nn.ReLU()

    def forward(self, input_id, mask):
        outputs = self.bert(input_ids=input_id, attention_mask=mask, return_dict=False)
        pooled_output = outputs[1]
        dropout_output = self.dropout(pooled_output)
        linear_output = self.linear(dropout_output)
        final_output = self.relu(linear_output)
        return final_output

if __name__ == "__main__":
    data_paths = {
        'train': './train.csv',
        'dev': './dev.csv',
        'test': './test.csv'
    }
    
    # 初始化 NewsClassifier
    news_classifier = NewsClassifier(data_paths=data_paths, label_path='./class.txt', model_path='./chinese_L-12_H-768_A-12', save_path='./model')
    
    # 加载训练好的模型权重
    model_path = os.path.join(news_classifier.save_path, 'best_model.pt')
    news_classifier.model.load_state_dict(torch.load(model_path))
    news_classifier.model.to(news_classifier.device)
    
    # 加载验证集和测试集
    dev_df = news_classifier.load_data(data_paths['dev']).reset_index(drop=True)
    test_df = news_classifier.load_data(data_paths['test']).reset_index(drop=True)
    
    # 获取验证集中的错误标记样本
    misclassified_dev_samples = news_classifier.get_misclassified_samples(dev_df)
    misclassified_dev_df = pd.DataFrame(misclassified_dev_samples)
    misclassified_dev_df.to_csv('./misclassified_dev_samples.csv', index=False, encoding='utf-8-sig')
    print("验证集中的错误标记样本已保存到 './misclassified_dev_samples.csv'")
    
    # 获取测试集中的错误标记样本
    misclassified_test_samples = news_classifier.get_misclassified_samples(test_df)
    misclassified_test_df = pd.DataFrame(misclassified_test_samples)
    misclassified_test_df.to_csv('./misclassified_test_samples.csv', index=False, encoding='utf-8-sig')
    print("测试集中的错误标记样本已保存到 './misclassified_test_samples.csv'")