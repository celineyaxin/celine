# create_sample.py
import pandas as pd
import logging
import json
from pathlib import Path
import random
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FlexibleDataSampler:
    def __init__(self):
        self.sampling_history = {}
    
    def create_primary_sample(self, input_file, output_file, sample_size=10000, random_state=42, 
                            filter_condition=None, stratify_column=None):
        """创建一级样本（大样本）- 保持CSV格式，支持筛选和分层抽样"""
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
            
            # 应用筛选条件（如果有）
            original_count = len(df)
            if filter_condition:
                df = self._apply_filter_condition(df, filter_condition)
                filtered_count = len(df)
                logging.info(f"筛选条件应用: 从{original_count}条记录中筛选出{filtered_count}条")
            
            # 分层抽样或简单随机抽样
            if len(df) <= sample_size:
                sampled_df = df.copy()
                logging.info("数据量小于样本量，使用全部数据")
            else:
                if stratify_column and stratify_column in df.columns:
                    # 分层抽样
                    sampled_df, _ = train_test_split(
                        df, 
                        train_size=sample_size, 
                        random_state=random_state, 
                        stratify=df[stratify_column]
                    )
                    logging.info(f"使用分层抽样，分层列: {stratify_column}")
                else:
                    # 简单随机抽样
                    sampled_df = df.sample(n=sample_size, random_state=random_state, replace=False)
                    logging.info("使用简单随机抽样")
            
            # 确保输出目录存在
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存一级样本（CSV格式）
            sampled_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            
            # 记录抽样信息 - JSON文件保存在一级样本同目录下
            sample_info = {
                'total_records': len(sampled_df),
                'random_state': random_state,
                'filter_condition': filter_condition,
                'stratify_column': stratify_column,
                'sampled_indices': sampled_df.index.tolist(),
                'subsamples': [],  # 用于记录所有子样本
                'next_start_index': 0  # 下一个起始位置
            }
            
            # JSON文件与一级样本同目录同名，扩展名为_info.json
            info_file = output_file.replace('.csv', '_info.json')
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(sample_info, f, ensure_ascii=False, indent=2)
            
            logging.info(f"一级样本保存: {output_file}")
            logging.info(f"状态文件保存: {info_file}")
            return sampled_df
            
        except Exception as e:
            logging.error(f"创建一级样本失败: {e}")
            raise
    
    def _apply_filter_condition(self, df, filter_condition):
        """应用筛选条件"""
        if isinstance(filter_condition, dict):
            column = filter_condition.get('column')
            value = filter_condition.get('value')
            if column and column in df.columns:
                filtered_df = df[df[column] == value]
                return filtered_df
        elif isinstance(filter_condition, str):
            try:
                filtered_df = df.query(filter_condition)
                return filtered_df
            except:
                logging.warning(f"无法解析筛选条件: {filter_condition}, 使用原始数据")
                return df
        else:
            logging.warning(f"不支持的筛选条件格式: {type(filter_condition)}, 使用原始数据")
            return df
    
    def create_subsample(self, primary_sample_file, subsample_size=1000, start_index=None, 
                        output_dir=None, filter_condition=None, stratify_column=None):
        """从一级样本创建二级子样本 - 自动管理位置"""
        
        # 读取抽样信息
        info_file = primary_sample_file.replace('.csv', '_info.json')
        with open(info_file, 'r', encoding='utf-8') as f:
            primary_info = json.load(f)
        
        # 自动确定起始位置
        if start_index is None:
            start_index = primary_info.get('next_start_index', 0)
        
        logging.info(f"创建二级子样本: 从{start_index}开始，取{subsample_size}条")
        
        try:
            # 读取一级样本
            primary_df = pd.read_csv(primary_sample_file)
            total_records = len(primary_df)
            
            # 应用筛选条件（如果提供）
            working_df = primary_df.copy()
            if filter_condition:
                working_df = self._apply_filter_condition(working_df, filter_condition)
                filtered_count = len(working_df)
                logging.info(f"子样本筛选条件应用: 筛选出{filtered_count}条")
            
            # 计算可用数据范围
            available_data = working_df.iloc[start_index:]
            actual_available = len(available_data)
            
            if actual_available <= 0:
                raise ValueError("没有可用的数据了")
            
            # 确定实际抽样大小
            actual_size = min(subsample_size, actual_available)
            
            # 如果请求的大小超过可用数据，提示用户
            if subsample_size > actual_available:
                logging.warning(f"请求大小{subsample_size}超过可用数据{actual_available}，使用全部可用数据")
            
            # 分层抽样或连续抽样
            if stratify_column and stratify_column in available_data.columns:
                if actual_size < len(available_data):
                    subsampled_df, _ = train_test_split(
                        available_data,
                        train_size=actual_size,
                        random_state=42,
                        stratify=available_data[stratify_column]
                    )
                    logging.info(f"子样本使用分层抽样，分层列: {stratify_column}")
                else:
                    subsampled_df = available_data
            else:
                subsampled_df = available_data.head(actual_size)
            
            # 生成输出文件名
            primary_stem = Path(primary_sample_file).stem
            
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = Path(primary_sample_file).parent
                
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 文件名包含筛选信息
            filter_suffix = ""
            if filter_condition:
                if isinstance(filter_condition, dict):
                    filter_suffix = f"_filter_{filter_condition.get('column')}_{filter_condition.get('value')}"
                else:
                    filter_suffix = "_filtered"
            
            stratify_suffix = f"_stratify_{stratify_column}" if stratify_column else ""
            
            output_file = output_path / f"{primary_stem}_from{start_index}_size{actual_size}{filter_suffix}{stratify_suffix}.xlsx"
            
            # 保存子样本
            subsampled_df.to_excel(output_file, index=False, engine='openpyxl')
            
            # 更新抽样信息
            subsample_info = {
                'start': start_index,
                'size': actual_size,
                'filter_condition': filter_condition,
                'stratify_column': stratify_column,
                'subsample_file': str(output_file),
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            primary_info['subsamples'].append(subsample_info)
            primary_info['next_start_index'] = start_index + actual_size
            
            # 更新JSON状态文件
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(primary_info, f, ensure_ascii=False, indent=2)
            
            next_start = primary_info['next_start_index']
            
            logging.info(f"二级子样本保存: {output_file}")
            logging.info(f"状态文件已更新: {info_file}")
            logging.info(f"下次可从第 {next_start} 条开始")
            
            return subsampled_df, next_start
            
        except Exception as e:
            logging.error(f"创建二级子样本失败: {e}")
            raise

    def get_sampling_status(self, primary_sample_file):
        """获取抽样状态"""
        info_file = primary_sample_file.replace('.csv', '_info.json')
        
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                primary_info = json.load(f)
            
            primary_df = pd.read_csv(primary_sample_file)
            total_records = len(primary_df)
            
            subsamples = primary_info.get('subsamples', [])
            total_used = sum([s['size'] for s in subsamples])
            remaining = total_records - total_used
            
            status = {
                'total_records': total_records,
                'used_records': total_used,
                'remaining_records': remaining,
                'next_start_index': primary_info.get('next_start_index', 0),
                'subsamples': subsamples
            }
            
            return status
        except Exception as e:
            logging.error(f"获取抽样状态失败: {e}")
            return None

# 主程序 - 支持交互式选择子样本大小
if __name__ == "__main__":
    sampler = FlexibleDataSampler()
    
    # 配置文件路径和参数
    INPUT_FILE = "/Users/chenyaxin/Desktop/websitdata/bert/results/是否明示/delete_hostility.csv"
    PRIMARY_SAMPLE_FILE = "/Users/chenyaxin/Desktop/审稿修改/分类数据/计算能力/明示投诉_prediction1_一级样本_10000条.csv"
    OUTPUT_DIR = "/Users/chenyaxin/Desktop/审稿修改/分类数据/计算能力"
    

    FILTER_CONDITION = {'column': 'prediction', 'value': 1}
    
    try:
        # 第一步：检查一级样本是否存在，如果不存在则创建
        if not Path(PRIMARY_SAMPLE_FILE).exists():
            logging.info("创建一级样本...")
            primary_df = sampler.create_primary_sample(
                input_file=INPUT_FILE,
                output_file=PRIMARY_SAMPLE_FILE,
                sample_size=10000,
                random_state=42,
                filter_condition=FILTER_CONDITION,  
                stratify_column=None
            )
            logging.info("一级样本创建完成")
        else:
            logging.info("一级样本已存在，跳过创建")
        
        # 第二步：获取当前状态
        status = sampler.get_sampling_status(PRIMARY_SAMPLE_FILE)
        if status is None:
            logging.error("无法获取抽样状态，程序退出")
            exit(1)
            
        print(f"\n=== 当前抽样状态 ===")
        print(f"总记录数: {status['total_records']}")
        print(f"已使用: {status['used_records']}")
        print(f"剩余: {status['remaining_records']}")
        print(f"下次开始位置: {status['next_start_index']}")
        
        # 显示已有的子样本
        if status['subsamples']:
            print(f"\n已有的子样本:")
            for i, sample in enumerate(status['subsamples'], 1):
                print(f"  {i}. {Path(sample['subsample_file']).name} (大小: {sample['size']}条)")
        
        # 第三步：交互式创建子样本
        remaining = status['remaining_records']
        
        if remaining <= 0:
            logging.info("所有数据都已抽样完毕！")
        else:
            print(f"\n=== 创建新子样本 ===")
            print(f"可用数据: {remaining}条")
            
            # 获取用户输入的子样本大小
            while True:
                try:
                    user_input = input(f"请输入子样本大小 (1-{remaining}), 或输入 'q' 退出: ")
                    
                    if user_input.lower() == 'q':
                        logging.info("用户退出程序")
                        break
                    
                    subsample_size = int(user_input)
                    
                    if subsample_size <= 0:
                        print("子样本大小必须大于0")
                        continue
                    
                    if subsample_size > remaining:
                        print(f"子样本大小不能超过剩余数据量 {remaining}")
                        continue
                    
                    # 创建子样本
                    logging.info(f"创建子样本，大小: {subsample_size}条")
                    subsample, next_index = sampler.create_subsample(
                        primary_sample_file=PRIMARY_SAMPLE_FILE,
                        subsample_size=subsample_size,
                        start_index=None,  # 自动从记录的位置开始
                        output_dir=OUTPUT_DIR,
                        filter_condition=FILTER_CONDITION,  # 不再筛选
                        stratify_column=None
                    )
                    
                    # 显示结果
                    new_status = sampler.get_sampling_status(PRIMARY_SAMPLE_FILE)
                    print(f"\n✅ 子样本创建成功!")
                    print(f"📊 文件: {Path(new_status['subsamples'][-1]['subsample_file']).name}")
                    print(f"📈 大小: {subsample_size}条")
                    print(f"📋 新状态: 已使用 {new_status['used_records']}/{new_status['total_records']}")
                    print(f"➡️  下次开始位置: {new_status['next_start_index']}")
                    
                    # 询问是否继续创建另一个子样本
                    if new_status['remaining_records'] > 0:
                        continue_choice = input(f"\n是否继续创建另一个子样本? [y/N]: ")
                        if continue_choice.lower() not in ['y', 'yes']:
                            break
                    else:
                        print("所有数据都已抽样完毕！")
                        break
                        
                except ValueError:
                    print("请输入有效的数字")
                except Exception as e:
                    print(f"创建子样本失败: {e}")
                    break
        
        # 最终状态显示
        final_status = sampler.get_sampling_status(PRIMARY_SAMPLE_FILE)
        if final_status:
            print(f"\n=== 最终抽样状态 ===")
            print(f"总记录数: {final_status['total_records']}")
            print(f"已使用: {final_status['used_records']}")
            print(f"剩余: {final_status['remaining_records']}")
            print(f"状态文件: {PRIMARY_SAMPLE_FILE.replace('.csv', '_info.json')}")
        
    except Exception as e:
        print(f"程序运行失败: {e}")