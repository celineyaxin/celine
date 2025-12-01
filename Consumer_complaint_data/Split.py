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
            
            # 如果补充样本只有投诉内容，添加bias_status列（假设都是"是"）
            if 'bias_status' not in supplement_df.columns:
                supplement_df['bias_status'] = '是'
                logging.info("补充样本自动添加bias_status='是'")
            
            # 为补充样本添加缺失的列（用NaN或默认值填充）
            for col in df.columns:
                if col not in supplement_df.columns and col not in ['投诉内容', 'bias_status']:
                    supplement_df[col] = None  # 或适当的默认值
            
            # 确保列顺序一致
            supplement_df = supplement_df[df.columns]
            
            # 合并数据
            df = pd.concat([df, supplement_df], ignore_index=True)
            logging.info(f"合并后总样本数: {len(df)}")
        
        # 检查必要的列是否存在
        required_columns = ['bias_status', '投诉内容']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"数据文件中缺少必要的列: {col}")
        
        # 再次检查并过滤bias_status为空的行
        initial_count_final = len(df)
        df = df[df['bias_status'].notna() & (df['bias_status'].str.strip() != '')]
        filtered_bias_count = initial_count_final - len(df)
        if filtered_bias_count > 0:
            logging.info(f"过滤掉 {filtered_bias_count} 条bias_status为空的行")
        
        # 打印数据概况
        logging.info(f"数据概况:")
        total_count = len(df)
        bias_counts = df['bias_status'].value_counts()
        for status, count in bias_counts.items():
            percentage = (count / total_count) * 100
            logging.info(f"  {status}: {count} 个 ({percentage:.2f}%)")
        
        return df
    
    def balance_dataset(self, df, positive_ratio=1, negative_ratio=2):
        """平衡数据集，按指定比例抽取正负样本，考虑多种优化策略"""
        logging.info("开始平衡数据集...")
        
        # 分离三类样本
        positive_samples = df[df['bias_status'] == '是'].copy()
        negative_samples = df[df['bias_status'] == '否'].copy()
        uncertain_samples = df[df['bias_status'] == '不确定'].copy()
        
        logging.info(f"正样本数量: {len(positive_samples)}")
        logging.info(f"负样本数量: {len(negative_samples)}")
        logging.info(f"不确定样本数量: {len(uncertain_samples)}")
        
        # 检查是否有足够的正样本
        if len(positive_samples) == 0:
            logging.error("错误: 没有找到正样本(bias_status='是')")
            raise ValueError("数据集中没有正样本，无法进行平衡")
        
        # 计算需要抽取的总负样本数量
        target_negative_count = len(positive_samples) * negative_ratio
        logging.info(f"目标负样本总数: {target_negative_count}")
        
        # 按照原始比例分配"否"和"不确定"的抽取数量
        total_negative_pool = len(negative_samples) + len(uncertain_samples)
        if total_negative_pool == 0:
            logging.error("错误: 没有找到负样本(bias_status='否'或'不确定')")
            raise ValueError("数据集中没有负样本，无法进行平衡")
        
        negative_ratio_original = len(negative_samples) / total_negative_pool
        uncertain_ratio_original = len(uncertain_samples) / total_negative_pool
        
        target_negative_count_negative = int(target_negative_count * negative_ratio_original)
        target_negative_count_uncertain = target_negative_count - target_negative_count_negative
        
        # 确保目标数量不超过可用样本数
        target_negative_count_negative = min(target_negative_count_negative, len(negative_samples))
        target_negative_count_uncertain = min(target_negative_count_uncertain, len(uncertain_samples))
        
        logging.info(f"目标'否'样本: {target_negative_count_negative}")
        logging.info(f"目标'不确定'样本: {target_negative_count_uncertain}")
        
        # 优化策略1: 优先抽取高质量的"否"样本
        # 如果有置信度信息，优先抽取高置信度的样本
        if 'confidence' in df.columns:
            negative_samples_sorted = negative_samples.sort_values('confidence', ascending=False)
            uncertain_samples_sorted = uncertain_samples.sort_values('confidence', ascending=False)
        else:
            # 如果没有置信度，使用其他策略
            negative_samples_sorted = negative_samples
            uncertain_samples_sorted = uncertain_samples
        
        # 优化策略2: 分层抽样 - 如果数据中有企业信息，按企业分层
        sampled_negative = pd.DataFrame()
        sampled_uncertain = pd.DataFrame()
        
        if '企业名称' in df.columns or '企业' in df.columns or '投诉商家' in df.columns:
            # 确定企业列名
            enterprise_cols = [col for col in ['企业名称', '企业', '投诉商家'] if col in df.columns]
            enterprise_col = enterprise_cols[0] if enterprise_cols else None
            
            if enterprise_col:
                # 对"否"样本按企业分层抽样
                negative_enterprise_counts = negative_samples_sorted[enterprise_col].value_counts()
                for enterprise, count in negative_enterprise_counts.items():
                    enterprise_samples = negative_samples_sorted[negative_samples_sorted[enterprise_col] == enterprise]
                    enterprise_ratio = count / len(negative_samples_sorted)
                    enterprise_target = max(1, int(target_negative_count_negative * enterprise_ratio))
                    
                    if len(enterprise_samples) >= enterprise_target:
                        sampled = enterprise_samples.sample(n=enterprise_target, random_state=self.random_seed)
                    else:
                        sampled = enterprise_samples
                    
                    sampled_negative = pd.concat([sampled_negative, sampled])
                
                # 对"不确定"样本按企业分层抽样
                uncertain_enterprise_counts = uncertain_samples_sorted[enterprise_col].value_counts()
                for enterprise, count in uncertain_enterprise_counts.items():
                    enterprise_samples = uncertain_samples_sorted[uncertain_samples_sorted[enterprise_col] == enterprise]
                    enterprise_ratio = count / len(uncertain_samples_sorted)
                    enterprise_target = max(1, int(target_negative_count_uncertain * enterprise_ratio))
                    
                    if len(enterprise_samples) >= enterprise_target:
                        sampled = enterprise_samples.sample(n=enterprise_target, random_state=self.random_seed)
                    else:
                        sampled = enterprise_samples
                    
                    sampled_uncertain = pd.concat([sampled_uncertain, sampled])
            else:
                # 如果没有企业信息，使用简单随机抽样
                sampled_negative = negative_samples_sorted.sample(
                    n=min(target_negative_count_negative, len(negative_samples_sorted)), 
                    random_state=self.random_seed
                )
                sampled_uncertain = uncertain_samples_sorted.sample(
                    n=min(target_negative_count_uncertain, len(uncertain_samples_sorted)), 
                    random_state=self.random_seed
                )
        else:
            # 如果没有企业信息，使用简单随机抽样
            sampled_negative = negative_samples_sorted.sample(
                n=min(target_negative_count_negative, len(negative_samples_sorted)), 
                random_state=self.random_seed
            )
            sampled_uncertain = uncertain_samples_sorted.sample(
                n=min(target_negative_count_uncertain, len(uncertain_samples_sorted)), 
                random_state=self.random_seed
            )
        
        # 如果抽样数量不足，从另一类补充
        total_sampled = len(sampled_negative) + len(sampled_uncertain)
        if total_sampled < target_negative_count:
            logging.warning(f"负样本数量不足，实际抽取: {total_sampled}, 目标: {target_negative_count}")
            # 可以调整策略，比如从另一类中补充
        
        # 合并正样本和抽样后的负样本
        balanced_df = pd.concat([positive_samples, sampled_negative, sampled_uncertain], ignore_index=True)
        
        # 打乱数据顺序
        balanced_df = balanced_df.sample(frac=1, random_state=self.random_seed).reset_index(drop=True)
        
        logging.info(f"平衡后数据集概况:")
        logging.info(f"总样本数: {len(balanced_df)}")
        bias_counts_balanced = balanced_df['bias_status'].value_counts()
        for status, count in bias_counts_balanced.items():
            percentage = (count / len(balanced_df)) * 100
            logging.info(f"  {status}: {count} 个 ({percentage:.2f}%)")
        
        return balanced_df
    
    def prepare_final_datasets(self, train_df, val_df, test_df):
        """准备最终数据集，只保留投诉内容和01标记列"""
        logging.info("准备最终数据集，只保留投诉内容和01标记列...")
        
        # 将bias_status转换为01标记
        def convert_label(status):
            return 1 if status == '是' else 0
        
        # 处理每个数据集
        def process_dataset(df):
            # 只保留投诉内容和转换后的标签
            processed_df = df[['投诉内容', 'bias_status']].copy()
            processed_df['label'] = processed_df['bias_status'].apply(convert_label)
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
        
        return train_processed, val_processed, test_processed
    
    def split_dataset(self, df, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """将数据集划分为训练集、验证集和测试集，使用分层抽样"""
        logging.info("开始划分数据集...")
        
        # 验证比例总和为1
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "比例总和必须为1"
        
        # 使用bias_status进行分层，确保标签分布均衡
        train_df, temp_df = train_test_split(
            df, 
            train_size=train_ratio,
            stratify=df['bias_status'],
            random_state=self.random_seed
        )
        
        # 第二次划分：验证集和测试集
        val_ratio_adjusted = val_ratio / (val_ratio + test_ratio)
        val_df, test_df = train_test_split(
            temp_df,
            train_size=val_ratio_adjusted,
            stratify=temp_df['bias_status'],
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
            bias_counts = df['bias_status'].value_counts()
            
            logging.info(f"\n{name}分布:")
            for status, count in bias_counts.items():
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
    INPUT_FILE = "/Users/chenyaxin/Desktop/审稿修改/分类数据/计算能力/代表性偏差分类_合并结果+补充样本.xlsx"
    SUPPLEMENT_FILE = None # 补充样本文件路径，如果没有设为None
    
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
        
        # 2. 平衡数据集 (1:2 正负样本比例)，使用优化策略
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