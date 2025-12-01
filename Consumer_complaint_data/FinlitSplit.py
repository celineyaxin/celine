import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import random
import logging
import os
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataBalancer:
    def __init__(self, random_seed=42):
        self.random_seed = random_seed
        random.seed(random_seed)
        np.random.seed(random_seed)
    
    def load_and_prepare_data(self, file_path, supplement_file_path=None):
        """加载Excel文件并准备数据，支持补充样本，过滤空白行"""
        logging.info(f"正在加载数据文件: {file_path}")
        df = pd.read_excel(file_path)
        
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
            
            # 过滤补充样本的空白行
            initial_supplement_count = len(supplement_df)
            supplement_df = supplement_df[supplement_df['投诉内容'].notna() & (supplement_df['投诉内容'].str.strip() != '')]
            filtered_supplement_count = initial_supplement_count - len(supplement_df)
            if filtered_supplement_count > 0:
                logging.info(f"过滤掉 {filtered_supplement_count} 条补充样本空白投诉内容行")
            
            # 检查补充样本的必要列
            if '投诉内容' not in supplement_df.columns:
                raise ValueError(f"补充样本文件中缺少必要的列: 投诉内容")
            
            # 如果补充样本只有投诉内容，添加标记列（假设都是"是"）
            if '标记' not in supplement_df.columns:
                supplement_df['标记'] = '是'
                logging.info("补充样本自动添加标记='是'")
            
            # 为补充样本添加缺失的列（用NaN或默认值填充）
            for col in df.columns:
                if col not in supplement_df.columns and col not in ['投诉内容', '标记']:
                    supplement_df[col] = None
            
            # 确保列顺序一致
            supplement_df = supplement_df[df.columns]
            
            # 合并数据
            df = pd.concat([df, supplement_df], ignore_index=True)
            logging.info(f"合并后总样本数: {len(df)}")
        
        # 检查必要的列是否存在
        required_columns = ['标记', '投诉内容']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"数据文件中缺少必要的列: {col}")
        
        # 再次检查并过滤标记为空的行
        initial_count_final = len(df)
        df = df[df['标记'].notna() & (df['标记'].str.strip() != '')]
        filtered_label_count = initial_count_final - len(df)
        if filtered_label_count > 0:
            logging.info(f"过滤掉 {filtered_label_count} 条标记为空的行")
        
        # 打印数据概况
        logging.info(f"数据概况:")
        total_count = len(df)
        label_counts = df['标记'].value_counts()
        for status, count in label_counts.items():
            percentage = (count / total_count) * 100
            logging.info(f"  {status}: {count} 个 ({percentage:.2f}%)")
        
        return df
    
    def balance_dataset(self, df, positive_ratio=1, negative_ratio=2):
        """平衡数据集，按指定比例抽取正负样本"""
        logging.info("开始平衡数据集...")
        
        # 分离四类样本
        positive_samples = df[df['标记'] == '是'].copy()
        negative_samples = df[df['标记'] == '否'].copy()
        dunning_samples = df[df['标记'] == '催收'].copy()
        uncertain_samples = df[df['标记'] == '不确定'].copy()
        
        logging.info(f"正样本数量: {len(positive_samples)}")
        logging.info(f"负样本数量: {len(negative_samples)}")
        logging.info(f"催收样本数量: {len(dunning_samples)}")
        logging.info(f"不确定样本数量: {len(uncertain_samples)}")
        
        # 检查是否有足够的正样本
        if len(positive_samples) == 0:
            logging.error("错误: 没有找到正样本(标记='是')")
            raise ValueError("数据集中没有正样本，无法进行平衡")
        
        # 计算需要抽取的总负样本数量
        target_negative_count = len(positive_samples) * negative_ratio
        logging.info(f"目标负样本总数: {target_negative_count}")
        
        # 合并负样本池（否 + 催收 + 不确定）
        negative_pool = pd.concat([negative_samples, dunning_samples, uncertain_samples], ignore_index=True)
        total_negative_pool = len(negative_pool)
        
        if total_negative_pool == 0:
            logging.error("错误: 没有找到负样本(标记='否'或'催收'或'不确定')")
            raise ValueError("数据集中没有负样本，无法进行平衡")
        
        # 计算原始负样本池中各类别的比例
        original_negative_count = len(negative_samples)
        original_dunning_count = len(dunning_samples)
        original_uncertain_count = len(uncertain_samples)
        
        negative_ratio_original = original_negative_count / total_negative_pool if total_negative_pool > 0 else 0
        dunning_ratio_original = original_dunning_count / total_negative_pool if total_negative_pool > 0 else 0
        uncertain_ratio_original = original_uncertain_count / total_negative_pool if total_negative_pool > 0 else 0
        
        # 计算各类别的目标抽样数量
        target_negative_count_negative = int(target_negative_count * negative_ratio_original)
        target_negative_count_dunning = int(target_negative_count * dunning_ratio_original)
        target_negative_count_uncertain = target_negative_count - target_negative_count_negative - target_negative_count_dunning
        
        # 确保目标数量不超过可用样本数
        target_negative_count_negative = min(target_negative_count_negative, original_negative_count)
        target_negative_count_dunning = min(target_negative_count_dunning, original_dunning_count)
        target_negative_count_uncertain = min(target_negative_count_uncertain, original_uncertain_count)
        
        logging.info(f"目标'否'样本: {target_negative_count_negative}")
        logging.info(f"目标'催收'样本: {target_negative_count_dunning}")
        logging.info(f"目标'不确定'样本: {target_negative_count_uncertain}")
        
        # 抽样策略：简单随机抽样（保持你原有的逻辑）
        sampled_negative = negative_samples.sample(
            n=min(target_negative_count_negative, len(negative_samples)), 
            random_state=self.random_seed
        ) if len(negative_samples) > 0 else pd.DataFrame()
        
        sampled_dunning = dunning_samples.sample(
            n=min(target_negative_count_dunning, len(dunning_samples)), 
            random_state=self.random_seed
        ) if len(dunning_samples) > 0 else pd.DataFrame()
        
        sampled_uncertain = uncertain_samples.sample(
            n=min(target_negative_count_uncertain, len(uncertain_samples)), 
            random_state=self.random_seed
        ) if len(uncertain_samples) > 0 else pd.DataFrame()
        
        # 如果抽样数量不足，重新调整
        total_sampled = len(sampled_negative) + len(sampled_dunning) + len(sampled_uncertain)
        if total_sampled < target_negative_count:
            logging.warning(f"负样本数量不足，实际抽取: {total_sampled}, 目标: {target_negative_count}")
            # 可以按比例从剩余样本中补充，这里保持简单逻辑
        
        # 合并正样本和抽样后的负样本
        balanced_df = pd.concat([
            positive_samples, 
            sampled_negative, 
            sampled_dunning, 
            sampled_uncertain
        ], ignore_index=True)
        
        # 打乱数据顺序
        balanced_df = balanced_df.sample(frac=1, random_state=self.random_seed).reset_index(drop=True)
        
        logging.info(f"平衡后数据集概况:")
        logging.info(f"总样本数: {len(balanced_df)}")
        label_counts_balanced = balanced_df['标记'].value_counts()
        for status, count in label_counts_balanced.items():
            percentage = (count / len(balanced_df)) * 100
            logging.info(f"  {status}: {count} 个 ({percentage:.2f}%)")
        
        return balanced_df
    
    def prepare_final_datasets(self, train_df, val_df, test_df):
        """准备最终数据集，只保留投诉内容和01标记列"""
        logging.info("准备最终数据集，只保留投诉内容和01标记列...")
        
        # 将标记转换为01标记
        def convert_label(status):
            return 1 if status == '是' else 0
        
        # 处理每个数据集
        def process_dataset(df):
            # 只保留投诉内容和转换后的标签
            processed_df = df[['投诉内容', '标记']].copy()
            processed_df['label'] = processed_df['标记'].apply(convert_label)
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
        for name, dataset in [("训练集", train_processed), ("验证集", val_processed), ("测试集", test_processed)]:
            label_dist = dataset['label'].value_counts()
            logging.info(f"{name}标签分布: 正例(1)={label_dist.get(1, 0)}, 负例(0)={label_dist.get(0, 0)}")
        
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
            stratify=df['标记'],
            random_state=self.random_seed
        )
        
        # 第二次划分：验证集和测试集
        val_ratio_adjusted = val_ratio / (val_ratio + test_ratio)
        val_df, test_df = train_test_split(
            temp_df,
            train_size=val_ratio_adjusted,
            stratify=temp_df['标记'],
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
            label_counts = df['标记'].value_counts()
            
            logging.info(f"\n{name}分布:")
            for status, count in label_counts.items():
                percentage = (count / len(df)) * 100
                logging.info(f"  {status}: {count} 个 ({percentage:.2f}%)")
    
    def save_datasets_to_desktop(self, train_df, val_df, test_df):
        """保存划分后的数据集到桌面（CSV格式）- 只保留投诉内容和01标记，不保留表头"""
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # 创建文件名 - 直接使用标准名称
        train_file = os.path.join(desktop_path, "train.csv")
        val_file = os.path.join(desktop_path, "dev.csv")  # 注意：验证集通常称为dev
        test_file = os.path.join(desktop_path, "test.csv")
        
        # 保存文件为CSV格式，使用UTF-8编码，不保留表头
        train_df.to_csv(train_file, index=False, encoding='utf-8-sig', header=False)
        val_df.to_csv(val_file, index=False, encoding='utf-8-sig', header=False)
        test_df.to_csv(test_file, index=False, encoding='utf-8-sig', header=False)
        
        logging.info(f"数据集已保存到桌面(CSV格式，无表头):")
        logging.info(f"训练集: {train_file}")
        logging.info(f"验证集: {val_file}")
        logging.info(f"测试集: {test_file}")
        
        return train_file, val_file, test_file

# 主程序
def main():
    # ========== 配置区域 ==========
    # 请根据您的实际情况修改以下路径
    INPUT_FILE = "/Users/chenyaxin/Desktop/审稿修改/分类数据/金融素养分类.xlsx"
    SUPPLEMENT_FILE = None  # 补充样本文件路径，如果没有设为None
    
    # 处理参数
    POSITIVE_RATIO = 1    # 正样本比例
    NEGATIVE_RATIO = 2    # 负样本比例（相对于正样本）
    TRAIN_RATIO = 0.7     # 训练集比例
    VAL_RATIO = 0.15      # 验证集比例
    TEST_RATIO = 0.15     # 测试集比例
    
    # ========== 执行区域 ==========
    
    # 创建数据平衡器
    balancer = DataBalancer(random_seed=42)
    
    try:
        # 1. 加载数据（包含补充样本）
        df = balancer.load_and_prepare_data(INPUT_FILE, SUPPLEMENT_FILE)
        
        # 2. 平衡数据集 (1:2 正负样本比例)
        balanced_df = balancer.balance_dataset(df, 
                                             positive_ratio=POSITIVE_RATIO, 
                                             negative_ratio=NEGATIVE_RATIO)
        
        # 3. 划分数据集 (70%训练, 15%验证, 15%测试)，使用分层抽样
        train_df, val_df, test_df = balancer.split_dataset(
            balanced_df, 
            train_ratio=TRAIN_RATIO, 
            val_ratio=VAL_RATIO, 
            test_ratio=TEST_RATIO
        )
        
        # 4. 准备最终数据集，只保留投诉内容和01标记列
        train_processed, val_processed, test_processed = balancer.prepare_final_datasets(
            train_df, val_df, test_df
        )
        
        # 5. 保存数据集到桌面（CSV格式）- 使用标准文件名，不保留表头
        balancer.save_datasets_to_desktop(train_processed, val_processed, test_processed)
        
        logging.info("数据处理完成！")
        
    except Exception as e:
        logging.error(f"处理过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    main()