# create_sample.py
import pandas as pd
import logging
import json
from pathlib import Path
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FlexibleDataSampler:
    def __init__(self):
        self.sampling_history = {}
    
    def create_primary_sample(self, input_file, output_file, sample_size=10000, random_state=42):
        """创建一级样本（大样本）- 保持CSV格式"""
        logging.info(f"创建一级样本: {sample_size}条")
        
        try:
            # 尝试多种编码读取CSV
            try:
                df = pd.read_csv(input_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(input_file, encoding='gbk')
                    logging.info("使用GBK编码读取文件")
                except:
                    df = pd.read_csv(input_file, encoding='latin-1')
                    logging.info("使用latin-1编码读取文件")
            
            if len(df) <= sample_size:
                sampled_df = df.copy()
                logging.info("数据量小于样本量，使用全部数据")
            else:
                sampled_df = df.sample(n=sample_size, random_state=random_state, replace=False)
            
            # 确保输出目录存在
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存一级样本（CSV格式）
            sampled_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            # 记录抽样信息
            sample_info = {
                'total_records': len(sampled_df),
                'random_state': random_state,
                'sampled_indices': sampled_df.index.tolist(),
                'used_indices': []
            }
            
            info_file = output_file.replace('.csv', '_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(sample_info, f, ensure_ascii=False, indent=2)
            
            logging.info(f"一级样本保存: {output_file}")
            return sampled_df
            
        except Exception as e:
            logging.error(f"创建一级样本失败: {e}")
            raise
    
    def create_subsample(self, primary_sample_file, subsample_size=1000, start_index=0, output_dir=None):
        """从一级样本创建二级子样本（从指定位置开始）- 输出Excel格式"""
        logging.info(f"创建二级子样本: 从{start_index}开始，取{subsample_size}条")
        
        try:
            # 读取一级样本
            primary_df = pd.read_csv(primary_sample_file)
            total_records = len(primary_df)
            
            # 读取抽样信息
            info_file = primary_sample_file.replace('.csv', '_info.json')
            with open(info_file, 'r', encoding='utf-8') as f:
                primary_info = json.load(f)
            
            # 计算结束位置
            end_index = min(start_index + subsample_size, total_records)
            actual_size = end_index - start_index
            
            if actual_size <= 0:
                raise ValueError("没有可用的数据了")
            
            # 提取子样本
            subsampled_df = primary_df.iloc[start_index:end_index].copy()
            
            # 生成输出文件名（Excel格式）
            primary_stem = Path(primary_sample_file).stem
            
            # 确定输出目录：如果指定了就用指定的，否则用一级样本所在目录
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = Path(primary_sample_file).parent
                
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / f"{primary_stem}_from{start_index}_size{actual_size}.xlsx"
            
            # 保存子样本（Excel格式）
            subsampled_df.to_excel(output_file, index=False, engine='openpyxl')
            
            # 更新抽样信息
            if 'used_ranges' not in primary_info:
                primary_info['used_ranges'] = []
            
            primary_info['used_ranges'].append({
                'start': start_index,
                'end': end_index,
                'size': actual_size,
                'subsample_file': str(output_file)
            })
            
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(primary_info, f, ensure_ascii=False, indent=2)
            
            logging.info(f"二级子样本保存: {output_file}")
            logging.info(f"下次可从第 {end_index} 条开始")
            
            return subsampled_df, end_index
            
        except Exception as e:
            logging.error(f"创建二级子样本失败: {e}")
            raise

    def get_next_start_index(self, primary_sample_file):
        """获取下一个可用的起始索引"""
        info_file = primary_sample_file.replace('.csv', '_info.json')
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                primary_info = json.load(f)
            
            if 'used_ranges' not in primary_info or not primary_info['used_ranges']:
                return 0
            
            last_end = max([r['end'] for r in primary_info['used_ranges']])
            return last_end
        
        except:
            return 0
    
    def get_sampling_status(self, primary_sample_file):
        """获取抽样状态"""
        info_file = primary_sample_file.replace('.csv', '_info.json')
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                primary_info = json.load(f)
            
            primary_df = pd.read_csv(primary_sample_file)
            total_records = len(primary_df)
            
            used_ranges = primary_info.get('used_ranges', [])
            total_used = sum([r['size'] for r in used_ranges])
            remaining = total_records - total_used
            
            status = {
                'total_records': total_records,
                'used_records': total_used,
                'remaining_records': remaining,
                'next_start_index': self.get_next_start_index(primary_sample_file),
                'used_ranges': used_ranges
            }
            
            return status
        except:
            return None

# 使用示例
if __name__ == "__main__":
    sampler = FlexibleDataSampler()
    
    try:
        # 第一步：创建一级样本（10000条）- CSV格式
        primary_df = sampler.create_primary_sample(
            input_file="/Users/chenyaxin/Desktop/信息规范/data/投诉内容汇总.csv",
            output_file="/Users/chenyaxin/Desktop/投诉数据_一级样本_10000条.csv",
            sample_size=10000,
            random_state=42
        )
        
        # 第二步：创建第一个二级子样本（1000条，从0开始）- Excel格式
        subsample1, next_index = sampler.create_subsample(
            primary_sample_file="/Users/chenyaxin/Desktop/投诉数据_一级样本_10000条.csv",
            subsample_size=1000,
            start_index=0,
            output_dir="/Users/chenyaxin/Desktop"  # 明确指定输出到桌面
        )
        
        # 第三步：创建第二个二级子样本（1000条，从上次结束位置开始）- Excel格式
        # 保留注释，下次运行时取消注释即可
        subsample2, next_index = sampler.create_subsample(
            primary_sample_file="/Users/chenyaxin/Desktop/投诉数据_一级样本_10000条.csv", 
            subsample_size=2000,
            start_index=next_index,  # 从上次结束位置开始
            output_dir="/Users/chenyaxin/Desktop"  # 明确指定输出到桌面
        )
        
        # 查看状态
        status = sampler.get_sampling_status("/Users/chenyaxin/Desktop/投诉数据_一级样本_10000条.csv")
        print(f"\n抽样状态:")
        print(f"总记录数: {status['total_records']}")
        print(f"已使用: {status['used_records']}")
        print(f"剩余: {status['remaining_records']}")
        print(f"下次开始位置: {status['next_start_index']}")
        
        print(f"\n生成的文件:")
        print(f"✅ 一级样本: /Users/chenyaxin/Desktop/投诉数据_一级样本_10000条.csv")
        print(f"✅ 二级子样本: /Users/chenyaxin/Desktop/投诉数据_一级样本_10000条_from0_size1000.xlsx")
        
        print(f"\n下次运行提示:")
        print(f"取消注释代码中的第三步，从第 {status['next_start_index']} 条开始继续抽样")
        
    except Exception as e:
        print(f"运行失败: {e}")