import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import random
import logging
import os
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataBalancerThreeClass:
    def __init__(self, random_seed=42):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
        self.label_column = None  # 存储实际使用的标签列名
    
    def find_label_column(self, df):
        """自动查找标签列名"""
        possible_names = ['标记 ', '标记', 'bias_status', 'label', '类别', '分类']
        for name in possible_names:
            if name in df.columns:
                logging.info(f"找到标签列: '{name}'")
                return name
        # 如果没有找到，打印所有列名供参考
        logging.error(f"未找到标签列，可用列名: {list(df.columns)}")
        raise ValueError("未找到标签列，请检查Excel文件中的列名")
    
    def load_and_prepare_data(self, file_path, supplement_file_path=None):
        """加载Excel文件并准备数据，支持补充样本，过滤空白行"""
        logging.info(f"正在加载数据文件: {file_path}")
        df = pd.read_excel(file_path)
        
        # 查找标签列
        self.label_column = self.find_label_column(df)
        
        # 过滤空白行 - 投诉内容为空或只有空白字符的行
        initial_count = len(df)
        df = df[df['投诉内容'].notna() & (df['投诉内容'].str.strip() != '')]
        filtered_count = initial_count - len(df)
        if filtered_count > 0:
            logging.info(f"过滤掉 {filtered_count} 条空白投诉内容行")
        
        # 如果有补充样本，加载并合并
        if supplement_file_path:
            logging.info(f"正在加载补充样本文件: {supplement_file_path}")
            supplement_df = pd.read_excel(supplement_file_path)
            
            # 查找补充样本的标签列
            supplement_label_column = self.find_label_column(supplement_df)
            
            # 过滤补充样本的空白行
            initial_supplement_count = len(supplement_df)
            supplement_df = supplement_df[supplement_df['投诉内容'].notna() & (supplement_df['投诉内容'].str.strip() != '')]
            filtered_supplement_count = initial_supplement_count - len(supplement_df)
            if filtered_supplement_count > 0:
                logging.info(f"过滤掉 {filtered_supplement_count} 条补充样本空白投诉内容行")
            
            # 检查补充样本的必要列
            if '投诉内容' not in supplement_df.columns:
                raise ValueError(f"补充样本文件中缺少必要的列: 投诉内容")
            
            # 如果补充样本只有投诉内容，添加标签列（假设都是"是"）
            if supplement_label_column not in supplement_df.columns:
                supplement_df[self.label_column] = '是'
                logging.info(f"补充样本自动添加{self.label_column}='是'")
            
            # 为补充样本添加缺失的列（用NaN或默认值填充）
            for col in df.columns:
                if col not in supplement_df.columns and col not in ['投诉内容', self.label_column]:
                    supplement_df[col] = None
            
            # 确保列顺序一致
            supplement_df = supplement_df[df.columns]
            
            # 合并数据
            df = pd.concat([df, supplement_df], ignore_index=True)
            logging.info(f"合并后总样本数: {len(df)}")
        
        # 检查必要的列是否存在
        required_columns = [self.label_column, '投诉内容']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"数据文件中缺少必要的列: {col}")
        
        # 再次检查并过滤标签列为空的行
        initial_count_final = len(df)
        df = df[df[self.label_column].notna() & (df[self.label_column].str.strip() != '')]
        filtered_label_count = initial_count_final - len(df)
        if filtered_label_count > 0:
            logging.info(f"过滤掉 {filtered_label_count} 条标签为空的行")
        
        # 打印数据概况
        logging.info(f"数据概况:")
        total_count = len(df)
        label_counts = df[self.label_column].value_counts()
        for status, count in label_counts.items():
            percentage = (count / total_count) * 100
            logging.info(f"  {status}: {count} 个 ({percentage:.2f}%)")
        
        return df
    
    def balance_dataset_three_class(self, df, ratios={'是': 1, '否': 1.5, '其他': 1}):
        """三分类数据平衡 - 可自定义比例
        
        Args:
            df: 原始数据框
            ratios: 各类别比例，例如 {'是': 1, '否': 1.5, '其他': 1} 表示是:否:其他=1:1.5:1
        """
        logging.info(f"开始三分类数据平衡 (比例: {ratios})...")
        
        # 分离三类样本
        positive_samples = df[df[self.label_column] == '是'].copy()
        negative_samples = df[df[self.label_column] == '否'].copy()
        other_samples = df[df[self.label_column].isin(['催收', '不确定'])].copy()
        
        logging.info(f"正样本('是')数量: {len(positive_samples)}")
        logging.info(f"负样本('否')数量: {len(negative_samples)}")
        logging.info(f"其他样本('催收'+'不确定')数量: {len(other_samples)}")
        
        # 以"是"为基准计算目标数量
        base_count = len(positive_samples)
        target_positive = int(base_count * ratios['是'])
        target_negative = int(base_count * ratios['否'])
        target_other = int(base_count * ratios['其他'])
        
        logging.info(f"目标数量 - 是: {target_positive}, 否: {target_negative}, 其他: {target_other}")
        
        # 检查是否有足够的样本
        if base_count == 0:
            logging.error("错误: 没有找到正样本(标记='是')")
            raise ValueError("数据集中没有正样本，无法进行平衡")
        
        # 从每类中抽取目标数量的样本
        sampled_positive = positive_samples.sample(
            n=min(target_positive, len(positive_samples)), 
            random_state=self.random_seed
        ) if len(positive_samples) > 0 else pd.DataFrame()
        
        sampled_negative = negative_samples.sample(
            n=min(target_negative, len(negative_samples)), 
            random_state=self.random_seed
        ) if len(negative_samples) > 0 else pd.DataFrame()
        
        sampled_other = other_samples.sample(
            n=min(target_other, len(other_samples)), 
            random_state=self.random_seed
        ) if len(other_samples) > 0 else pd.DataFrame()
        
        # 合并样本
        balanced_df = pd.concat([
            sampled_positive, 
            sampled_negative, 
            sampled_other
        ], ignore_index=True)
        
        # 打乱顺序
        balanced_df = balanced_df.sample(frac=1, random_state=self.random_seed).reset_index(drop=True)
        
        # 打印平衡后概况
        logging.info(f"平衡后数据集概况 (比例 {ratios['是']}:{ratios['否']}:{ratios['其他']}):")
        logging.info(f"总样本数: {len(balanced_df)}")
        label_counts = balanced_df[self.label_column].value_counts()
        for label, count in label_counts.items():
            percentage = (count / len(balanced_df)) * 100
            logging.info(f"  {label}: {count} 个 ({percentage:.2f}%)")
        
        return balanced_df
    
    def prepare_final_datasets_three_class(self, train_df, val_df, test_df):
        """准备三分类最终数据集"""
        logging.info("准备三分类最终数据集，只保留投诉内容和三分类标记...")
        
        # 将标记转换为三分类数字标记
        def convert_label_three_class(status):
            if status == '是':
                return 0
            elif status == '否':
                return 1
            else:  # 催收、不确定等
                return 2
        
        # 处理每个数据集
        def process_dataset(df):
            # 只保留投诉内容和转换后的标签
            processed_df = df[['投诉内容', self.label_column]].copy()
            processed_df['label'] = processed_df[self.label_column].apply(convert_label_three_class)
            processed_df = processed_df[['投诉内容', 'label']]
            
            # 最终检查，确保没有空值
            initial_count = len(processed_df)
            processed_df = processed_df[
                processed_df['投诉内容'].notna() & 
                (processed_df['投诉内容'].str.strip() != '') &
                processed_df['label'].notna()
            ]
            filtered_count = initial_count - len(processed_df)
            if filtered_count > 0:
                logging.info(f"过滤掉 {filtered_count} 条最终数据中的无效行")
            
            return processed_df
        
        train_processed = process_dataset(train_df)
        val_processed = process_dataset(val_df)
        test_processed = process_dataset(test_df)
        
        # 打印处理后的数据集信息
        logging.info(f"训练集: {len(train_processed)}条")
        logging.info(f"验证集: {len(val_processed)}条")
        logging.info(f"测试集: {len(test_processed)}条")
        
        # 打印标签分布
        label_mapping = {0: '是', 1: '否', 2: '其他'}
        for name, dataset in [("训练集", train_processed), ("验证集", val_processed), ("测试集", test_processed)]:
            label_dist = dataset['label'].value_counts().sort_index()
            logging.info(f"{name}标签分布: ")
            for label, count in label_dist.items():
                label_name = label_mapping.get(label, '未知')
                percentage = (count / len(dataset)) * 100
                logging.info(f"  类别{label}({label_name}): {count}条 ({percentage:.2f}%)")
        
        return train_processed, val_processed, test_processed
    
    def split_dataset(self, df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """将数据集划分为训练集、验证集和测试集，使用分层抽样"""
        logging.info("开始划分数据集...")
        
        # 验证比例总和为1
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "比例总和必须为1"
        
        # 使用标记进行分层，确保标签分布均衡
        train_df, temp_df = train_test_split(
            df, 
            train_size=train_ratio,
            stratify=df[self.label_column],
            random_state=self.random_seed
        )
        
        # 第二次划分：验证集和测试集
        val_ratio_adjusted = val_ratio / (val_ratio + test_ratio)
        val_df, test_df = train_test_split(
            temp_df,
            train_size=val_ratio_adjusted,
            stratify=temp_df[self.label_column],
            random_state=self.random_seed
        )
        
        # 打印划分结果
        self._print_split_statistics(train_df, val_df, test_df)
        
        return train_df, val_df, test_df
    
    def _print_split_statistics(self, train_df, val_df, test_df):
        """打印数据集划分的统计信息"""
        logging.info("数据集划分完成:")
        total_count = len(train_df) + len(val_df) + len(test_df)
        logging.info(f"训练集: {len(train_df)} 条 ({len(train_df)/total_count*100:.1f}%)")
        logging.info(f"验证集: {len(val_df)} 条 ({len(val_df)/total_count*100:.1f}%)")
        logging.info(f"测试集: {len(test_df)} 条 ({len(test_df)/total_count*100:.1f}%)")
        
        for name, df in [("训练集", train_df), ("验证集", val_df), ("测试集", test_df)]:
            label_counts = df[self.label_column].value_counts()
            
            logging.info(f"\n{name}分布:")
            for status, count in label_counts.items():
                percentage = (count / len(df)) * 100
                logging.info(f"  {status}: {count} 个 ({percentage:.2f}%)")
    
    def save_datasets_to_desktop(self, train_df, val_df, test_df):
        """保存划分后的数据集到桌面（CSV格式）- 只保留投诉内容和三分类标记，不保留表头"""
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # 创建文件名 - 添加三分类标识
        train_file = os.path.join(desktop_path, "train.csv")
        val_file = os.path.join(desktop_path, "dev.csv")
        test_file = os.path.join(desktop_path, "test.csv")
        
        # 保存文件为CSV格式，使用UTF-8编码，不保留表头
        train_df.to_csv(train_file, index=False, encoding='utf-8-sig', header=False)
        val_df.to_csv(val_file, index=False, encoding='utf-8-sig', header=False)
        test_df.to_csv(test_file, index=False, encoding='utf-8-sig', header=False)
        
        logging.info(f"三分类数据集已保存到桌面(CSV格式，无表头):")
        logging.info(f"训练集: {train_file}")
        logging.info(f"验证集: {val_file}")
        logging.info(f"测试集: {test_file}")
        
        return train_file, val_file, test_file

# 主程序
def main():
    """三分类主程序 - 可自定义比例"""
    # ========== 配置区域 ==========
    INPUT_FILE = "/Users/chenyaxin/Desktop/审稿修改/分类数据/金融素养分类.xlsx"
    SUPPLEMENT_FILE = None  # 补充样本文件路径，如果没有设为None
    
    # 三分类参数 - 可调整比例
    RATIOS = {'是': 1, '否': 1.5, '其他': 1}  # 是:否:其他 = 1:1.5:1
    TRAIN_RATIO = 0.7     # 训练集比例
    VAL_RATIO = 0.15      # 验证集比例
    TEST_RATIO = 0.15     # 测试集比例
    
    # ========== 执行区域 ==========
    
    # 创建数据平衡器
    balancer = DataBalancerThreeClass(random_seed=42)
    
    try:
        # 1. 加载数据（包含补充样本）
        df = balancer.load_and_prepare_data(INPUT_FILE, SUPPLEMENT_FILE)
        
        # 2. 三分类数据平衡 (可自定义比例)
        balanced_df = balancer.balance_dataset_three_class(df, ratios=RATIOS)
        
        # 3. 划分数据集 (70%训练, 15%验证, 15%测试)，使用分层抽样
        train_df, val_df, test_df = balancer.split_dataset(
            balanced_df, 
            train_ratio=TRAIN_RATIO, 
            val_ratio=VAL_RATIO, 
            test_ratio=TEST_RATIO
        )
        
        # 4. 准备三分类最终数据集，只保留投诉内容和三分类标记列
        train_processed, val_processed, test_processed = balancer.prepare_final_datasets_three_class(
            train_df, val_df, test_df
        )
        
        # 5. 保存三分类数据集到桌面（CSV格式）- 使用标准文件名，不保留表头
        balancer.save_datasets_to_desktop(train_processed, val_processed, test_processed)
        
        logging.info("三分类数据处理完成！")
        
        # 打印标签映射说明
        logging.info("\n三分类标签映射说明:")
        logging.info("  0 -> 是")
        logging.info("  1 -> 否")
        logging.info("  2 -> 其他(催收/不确定)")
        
    except Exception as e:
        logging.error(f"三分类处理过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main()