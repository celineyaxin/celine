import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel
import pandas as pd
import numpy as np
import os
from tqdm import tqdm

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.utils.class_weight import compute_class_weight

from nlpaug.augmenter.word import SynonymAug, ContextualWordEmbsAug
import nlpaug.flow as naf
import random

import nltk

# 确保必要的NLTK资源已下载
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('corpora/wordnet')
except LookupError:
    print("下载所需的NLTK资源...")
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    print("NLTK资源下载完成")

from transformers import BertForMaskedLM, BertTokenizer
import torch
import random

LABEL2ID = {
    0: 0,   # 类别0：原始标签0和24
    24: 0,  # 类别0：原始标签0和24
    
    11: 1,  # 类别1：原始标签11和13
    13: 1,  # 类别1：原始标签11和13
    
    12: 2,  # 类别2：原始标签12
    
    21: 3,  # 类别3：原始标签21和32
    32: 4,  # 类别3：原始标签21和32
    
    22: 5,  # 类别4：原始标签22
    23: 6,  # 类别5：原始标签23
    31: 7   # 类别6：原始标签31
}

NUM_CLASSES = len(set(LABEL2ID.values()))
ID2LABEL = {
    0: 0,   # 类别0 → 原始标签0
    1: 11,  # 类别1 → 原始标签11
    2: 12,  # 类别2 → 原始标签12
    3: 21,  # 类别3 → 原始标签21
    4: 32,  # 类别4 → 原始标签22
    5: 22,  # 类别5 → 原始标签23
    6: 23,   # 类别6 → 原始标签31
    7: 31   # 类别6 → 原始标签31
}

class CategoryAwareAugmenter:
    def __init__(self, model_path, device='cuda'):
        self.model = BertForMaskedLM.from_pretrained(model_path).to(device)
        self.tokenizer = BertTokenizer.from_pretrained(model_path)
        self.device = device
        self.model.eval()
        self.max_length = 512
        
        # 定义每个类别的保护词和替换策略
        self.category_strategies = {
            11: {"protected": ["诱导", "话术", "套路"], "replace": ["怂恿", "引导", "劝说", "消费", "购买"]},
            12: {"protected": ["充值", "会员", "承诺", "放贷"], "replace": ["预存", "VIP", "保证", "贷款"]},
            13: {"protected": ["冒充", "平台"], "replace": ["假冒", "伪装", "系统", "网站"]},
            14: {"protected": ["还款", "障碍", "逾期"], "replace": ["偿还", "阻碍", "拖欠", "延期"]},
            21: {"protected": ["强制", "搭售", "捆绑"], "replace": ["强迫", "搭配", "绑定", "保险"]},
            22: {"protected": ["强制", "下款", "同意"], "replace": ["强行", "放款", "许可", "贷款"]},
            23: {"protected": ["自动", "划扣", "授权"], "replace": ["自行", "扣款", "批准", "账户"]},
            24: {"protected": ["精准", "推荐", "信息"], "replace": ["精确", "推销", "资料", "个人"]},
            31: {"protected": ["高利贷", "利率", "利息"], "replace": ["高息", "费率", "息费", "法定"]},
            32: {"protected": ["隐藏", "费用", "额外"], "replace": ["隐瞒", "收费", "附加", "未告知"]},
        }
    
    def get_category_strategy(self, label):
        """获取类别的增强策略"""
        # 将映射后的标签转换回原始标签
        original_label = ID2LABEL.get(label, label)
        return self.category_strategies.get(original_label, {})
    
    def augment(self, text, label=None, num_replacements=3):
        """使用类别感知的增强策略"""
        if not text.strip():
            return text
        
        try:
            # 分词并截断
            tokens = self.tokenizer.tokenize(text)
            tokens = tokens[:self.max_length-2]
            
            if len(tokens) < 2:
                return text
            
            # 获取类别的增强策略
            strategy = self.get_category_strategy(label)
            protected_terms = strategy.get("protected", [])
            replace_suggestions = strategy.get("replace", [])
            
            # 选择可替换的位置（避开保护词）
            available_positions = [
                i for i in range(1, len(tokens)-1) 
                if tokens[i] not in protected_terms
            ]
            
            if not available_positions:
                return text
            
            # 确定替换数量（最多替换20%的token）
            max_replace = max(1, int(len(tokens) * 0.2))
            num_replacements = min(num_replacements, max_replace, len(available_positions))
            replace_positions = random.sample(available_positions, num_replacements)
            
            # 创建掩码输入
            masked_tokens = tokens.copy()
            for pos in replace_positions:
                masked_tokens[pos] = '[MASK]'
            
            # 添加特殊token
            input_tokens = ['[CLS]'] + masked_tokens + ['[SEP]']
            input_ids = self.tokenizer.convert_tokens_to_ids(input_tokens)
            input_ids = torch.tensor([input_ids]).to(self.device)
            attention_mask = torch.ones_like(input_ids)
            
            # 预测
            with torch.no_grad():
                outputs = self.model(input_ids, attention_mask=attention_mask)
                logits = outputs.logits[0]
            
            # 替换预测的token
            new_tokens = tokens.copy()
            for pos in replace_positions:
                pred_idx = pos + 1  # 考虑[CLS]偏移
                
                # 获取top-k预测
                top_k = torch.topk(logits[pred_idx], k=10)
                top_tokens = [
                    self.tokenizer.convert_ids_to_tokens(idx.item()) 
                    for idx in top_k.indices
                ]
                
                # 过滤无效token
                valid_tokens = [
                    t for t in top_tokens 
                    if t not in ['[CLS]','[SEP]','[PAD]','[UNK]','[MASK]'] 
                    and not t.startswith('##')
                    and not any(char in t for char in '[]')
                ]
                
                # 优先使用类别相关的建议词
                if replace_suggestions:
                    suggested = [t for t in valid_tokens if t in replace_suggestions]
                    if suggested:
                        new_token = random.choice(suggested[:3])
                        new_tokens[pos] = new_token
                        continue
                
                # 如果没有建议词，从有效token中选择
                if valid_tokens:
                    new_token = random.choice(valid_tokens[:3])
                    new_tokens[pos] = new_token
            
            return self.tokenizer.convert_tokens_to_string(new_tokens)
        
        except Exception as e:
            print(f"增强时出错: {e}")
            return text

# LABEL2ID = {
#     0: 0,   # 类别0：原始标签0和24
#     24: 0,  # 类别0：原始标签0和24
    
#     11: 1,  # 类别1：原始标签11和13
#     13: 1,  # 类别1：原始标签11和13
    
#     12: 1,  # 类别2：原始标签12
    
#     21: 2,  # 类别3：原始标签21和32
#     32: 2,  # 类别3：原始标签21和32
    
#     22: 2,  # 类别4：原始标签22
#     23: 2,  # 类别5：原始标签23
#     31: 0   # 类别6：原始标签31
# }
# NUM_CLASSES = 3  # 二分类只需要2个类别

# ID2LABEL = {
#     0: 0,   # 负类
#     1: 1,    # 正类
#     2: 2
# }

def plot_text_length_distribution(df):
    """
    绘制数据集中文本长度的直方图。
    
    参数:
    df - 包含文本数据的pandas DataFrame
    """
    # 设置全局字体为SimHei，这是一种支持中文的字体
    plt.rcParams['font.sans-serif'] = ['SimHei']
    # 解决保存图像时负号'-'显示为方块的问题
    plt.rcParams['axes.unicode_minus'] = False

    # 计算字符串长度并统计分布
    length_counts = df['text'].apply(len).value_counts().sort_index()

    # 绘制直方图
    plt.hist(length_counts.index, bins=len(length_counts), weights=length_counts.values)
    plt.xlabel('文本长度')
    plt.ylabel('频数')
    plt.title('字符串长度分布直方图')
    plt.show()

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
        self.model = BertClassifier(num_classes=NUM_CLASSES, model_path=self.model_path).to(self.device)
        
        self.min_samples_threshold = 150  # 少于这个数的类别需要增强
        self.augment_per_sample = 5   
        self.augmenter = CategoryAwareAugmenter(
            model_path=model_path, 
            device=self.device.type
        )

        train_df = self.load_data(self.data_paths['train'])
        train_df = self.augment_small_classes(train_df)
        dev_df = self.load_data(self.data_paths['dev'])
        self.train_dataset = self.create_dataset(train_df)
        self.dev_dataset = self.create_dataset(dev_df)
 
        y = train_df['label'].values
        weights = compute_class_weight('balanced', classes=np.unique(y), y=y)
        weights = torch.tensor(weights, dtype=torch.float).to(self.device)
        self.criterion = nn.CrossEntropyLoss(weight=weights)
    
    def augment_small_classes(self, df):
        """针对小样本类别进行数据增强"""
        # 统计各类别样本量
        class_counts = df['label'].value_counts().to_dict()
        print("原始类别分布:")
        print(class_counts)
        
        # 找出需要增强的小样本类别
        small_classes = [
            label for label, count in class_counts.items() 
            if count < self.min_samples_threshold
        ]
        
        if not small_classes:
            print("没有需要增强的小样本类别")
            return df
        
        print(f"需要增强的小样本类别: {small_classes}")
        augmented_data = []
        
        # 只对小样本类别的数据进行增强
        small_samples = df[df['label'].isin(small_classes)]
        print(f"将对 {len(small_samples)} 个小样本进行增强...")
        
        for _, row in tqdm(small_samples.iterrows(), total=len(small_samples), desc="增强小样本"):
            # 对每个小样本生成多个增强版本
            for _ in range(self.augment_per_sample):
                # 传入标签以进行类别感知增强
                aug_text = self.augmenter.augment(row['text'], label=row['label'])
                augmented_data.append({
                    'text': aug_text,
                    'label': row['label']
                })
        
        augmented_df = pd.DataFrame(augmented_data)
        
        # 合并原始数据和增强数据
        combined_df = pd.concat([df, augmented_df], ignore_index=True)
        
        # 打印增强后的分布
        print("\n增强后类别分布:")
        print(combined_df['label'].value_counts().sort_index())
        
        return combined_df
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
        df['label'] = df['label'].astype(int).map(LABEL2ID)
        valid_labels = set(range(NUM_CLASSES))
        invalid_labels = set(df['label']) - valid_labels
        if invalid_labels:
            raise ValueError(f"发现无效标签: {invalid_labels}")
            
        print(f"类别分布:\n{df['label'].value_counts().sort_index()}")
        return df

    def create_dataset(self, df):
        texts = [self.tokenizer(
            text, 
            padding='max_length', 
            max_length=512, 
            truncation=True, 
            return_tensors="pt"
        ) for text in df["text"]]
        labels = df['label'].values
        return MyDataset(texts, labels)
    def train(self, epochs, batch_size, lr):
        train_loader = DataLoader(self.train_dataset, batch_size=batch_size, shuffle=True)
        dev_loader = DataLoader(self.dev_dataset, batch_size=batch_size)

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        # self.optimizer = torch.optim.AdamW(  # 使用AdamW代替Adam
        #     self.model.parameters(), 
        #     lr=lr,
        #     weight_decay=0.01  # L2正则化
        # )
        best_dev_acc = 0
        for epoch in range(epochs):
            print(f"\nEpoch {epoch + 1}/{epochs}")
            self._train_epoch(train_loader, batch_size)
            val_acc = self._evaluate_epoch(dev_loader)
            if val_acc > best_dev_acc:
                best_dev_acc = val_acc
                self._save_model('best_model.pt')
                print(f"Save best model,TestAccuracy: {val_acc:.4f}")
    def _train_epoch(self, train_loader, batch_size):
        self.model.train()
        total_loss = 0
        total_correct = 0
        total_samples = 0
        
        for inputs, labels in tqdm(train_loader, desc="train"):
            input_ids = inputs['input_ids'].squeeze(1).to(self.device)
            attention_mask = inputs['attention_mask'].to(self.device)
            labels = labels.to(self.device)
            
            # 前向传播
            outputs = self.model(input_ids, attention_mask)
            loss = self.criterion(outputs, labels)
            
            # 反向传播
            loss.backward()
            self.optimizer.step()
            self.optimizer.zero_grad()
            _, predicted = torch.max(outputs, 1)
            total_correct += (predicted == labels).sum().item()
            total_loss += loss.item() * labels.size(0)
            total_samples += labels.size(0)
            
        avg_loss = total_loss / total_samples
        avg_acc = total_correct / total_samples
        print(f"TrainLoss: {avg_loss:.4f} | TrainAccuracy: {avg_acc:.4f}")
    
    def _evaluate_epoch(self, dev_loader):
        self.model.eval()
        total_correct = 0
        total_loss = 0
        total_samples = 0
        with torch.no_grad():
            for inputs, labels in tqdm(dev_loader, desc="dev"):
                input_ids = inputs['input_ids'].squeeze(1).to(self.device)
                attention_mask = inputs['attention_mask'].to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(input_ids, attention_mask)
                loss = self.criterion(outputs, labels)
                
                _, predicted = torch.max(outputs, 1)
                total_correct += (predicted == labels).sum().item()
                total_loss += loss.item() * labels.size(0)
                total_samples += labels.size(0)

        avg_loss = total_loss / total_samples
        avg_acc = total_correct / total_samples
        print(f"DevLoss: {avg_loss:.4f} | DevAccuracy: {avg_acc:.4f}")
        return avg_acc
    
    def _save_model(self, save_name):
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        save_path = os.path.join(self.save_path, save_name)
        torch.save(self.model.state_dict(), save_path)
        print(f"模型保存至: {save_path}")
    
    def evaluate(self, test_df):
        self.model.eval()
        test_dataset = self.create_dataset(test_df)
        test_loader = DataLoader(test_dataset, batch_size=32)
        
        total_correct = 0
        total_samples = 0
        
        with torch.no_grad():
            for inputs, labels in tqdm(test_loader, desc="test"):
                input_ids = inputs['input_ids'].squeeze(1).to(self.device)
                attention_mask = inputs['attention_mask'].to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(input_ids, attention_mask)
                _, predicted = torch.max(outputs, 1)
                total_correct += (predicted == labels).sum().item()
                total_samples += labels.size(0)
        accuracy = total_correct / total_samples
        print(f'TestAccuracy: {accuracy:.4f}')
        return accuracy
    
    def predict(self, text):
        self.model.eval()
        inputs = self.tokenizer(
            text, 
            padding='max_length', 
            max_length=512, 
            truncation=True, 
            return_tensors="pt"
        )
        input_ids = inputs['input_ids'].to(self.device)
        attention_mask = inputs['attention_mask'].to(self.device)
        
        with torch.no_grad():
            outputs = self.model(input_ids.squeeze(1), attention_mask)
        
        # 使用全局ID2LABEL映射返回原始标签
        pred_id = outputs.argmax(dim=1).item()
        return ID2LABEL[pred_id]
class MyDataset(Dataset):
    def __init__(self, texts, labels):
        self.texts = texts
        self.labels = labels

    def __getitem__(self, idx):
        return self.texts[idx], self.labels[idx]

    def __len__(self):
        return len(self.labels)

class BertClassifier(nn.Module):
    def __init__(self, num_classes, model_path):
        super(BertClassifier, self).__init__()
        self.bert = BertModel.from_pretrained(model_path)
        self.dropout = nn.Dropout(0.5)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(
            input_ids=input_ids, 
            attention_mask=attention_mask, 
            return_dict=False
        )
        pooled_output = outputs[1]
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        return logits
    
if __name__ == "__main__":

    data_paths = {
        'train': './train.csv',
        'dev': './dev.csv',
        'test': './test.csv'
    }
    news_classifier = NewsClassifier(data_paths = data_paths, label_path = './class.txt', model_path = './chinese_L-12_H-768_A-12', save_path = './model')
    news_classifier.train(epochs=10, batch_size=32, lr=1e-5)

    test_df = news_classifier.load_data(data_paths['test'])
    news_classifier.model.load_state_dict(torch.load(os.path.join(news_classifier.save_path, 'best_model.pt')))
    news_classifier.evaluate(test_df)
    # 预测
    while True:
        text = input('which type of financial fraud:')
        print(news_classifier.predict(text))