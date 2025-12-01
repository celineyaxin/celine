# create_sample.py
import pandas as pd
import logging
import json
from pathlib import Path
import random
import hashlib
from sklearn.model_selection import train_test_split
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FlexibleDataSampler:
    def __init__(self, input_file, output_dir, filter_condition=None):
        self.input_file = input_file
        self.output_dir = Path(output_dir)
        self.status_file = self.output_dir / "sampling_status.json"
        self.filter_condition = filter_condition  # 存储筛选条件
        
        # 初始化状态
        self.status = self._load_status()
        
        # 缓存已抽样的投诉编号
        self.sampled_complaint_ids_cache = None
        self.cache_valid = False
    
    def _load_status(self):
        """加载抽样状态"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                # 确保状态中有必要的键
                if 'sampled_complaint_ids' not in status:
                    status['sampled_complaint_ids'] = []
                if 'generated_files' not in status:
                    status['generated_files'] = []
                return status
            except Exception as e:
                logging.warning(f"加载状态文件失败: {e}")
        
        # 初始化新状态
        return {
            'original_file': str(self.input_file),
            'output_dir': str(self.output_dir),
            'filter_condition': self.filter_condition,
            'created_time': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'sampled_complaint_ids': [],
            'generated_files': []
        }
    
    def _save_status(self):
        """保存抽样状态"""
        self.status['last_updated'] = datetime.now().isoformat()
        self.status['filter_condition'] = self.filter_condition  # 保存筛选条件
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存状态文件失败: {e}")
    
    def get_existing_complaint_ids(self, force_rescan=False):
        """获取已抽样的投诉编号（使用缓存避免重复扫描）"""
        if not force_rescan and self.sampled_complaint_ids_cache is not None and self.cache_valid:
            return self.sampled_complaint_ids_cache
        
        logging.info("扫描输出目录中的样本文件...")
        sampled_complaint_ids = set()
        
        # 查找所有CSV和Excel样本文件
        csv_files = list(self.output_dir.glob("*.csv"))
        excel_files = list(self.output_dir.glob("*.xlsx"))
        all_files = csv_files + excel_files
        
        for file in all_files:
            try:
                # 跳过状态文件
                if file.name == "sampling_status.json":
                    continue
                    
                # 根据文件类型读取
                if file.suffix == '.csv':
                    df = pd.read_csv(file)
                else:  # .xlsx
                    df = pd.read_excel(file)
                
                # 检查是否有投诉编号列
                if not df.empty and '投诉编号' in df.columns:
                    complaint_ids = df['投诉编号'].dropna().astype(str).tolist()
                    sampled_complaint_ids.update(complaint_ids)
                    
            except Exception as e:
                logging.warning(f"读取文件失败 {file}: {e}")
        
        # 更新缓存
        self.sampled_complaint_ids_cache = list(sampled_complaint_ids)
        self.cache_valid = True
        
        logging.info(f"扫描完成: 找到 {len(sampled_complaint_ids)} 个已抽样投诉编号")
        return self.sampled_complaint_ids_cache
    
    def remove_duplicates_by_content(self, df, content_column='投诉内容'):
        """根据投诉内容去重"""
        if content_column not in df.columns:
            logging.warning(f"数据框中没有找到 '{content_column}' 列，跳过去重")
            return df
            
        # 记录去重前的数据量
        original_count = len(df)
        
        # 创建投诉内容的哈希值，用于去重
        df = df.copy()
        df['content_hash'] = df[content_column].fillna('').apply(
            lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest()
        )
        
        # 去重，保留第一个出现的重复项
        df_deduplicated = df.drop_duplicates(subset=['content_hash'], keep='first')
        
        # 删除临时列
        df_deduplicated = df_deduplicated.drop('content_hash', axis=1)
        
        # 记录去重结果
        removed_count = original_count - len(df_deduplicated)
        logging.info(f"去重完成: 原始 {original_count} 条，去重后 {len(df_deduplicated)} 条，移除 {removed_count} 条重复数据")
        
        return df_deduplicated
    
    def get_available_data(self):
        """获取可用的数据（先应用筛选条件，然后排除已抽样数据并去重）"""
        try:
            # 读取原始数据
            try:
                df = pd.read_csv(self.input_file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(self.input_file, encoding='gbk')
                except:
                    df = pd.read_csv(self.input_file, encoding='latin-1')
            
            # 先应用筛选条件（如果有）
            if self.filter_condition:
                df = self._apply_filter_condition(df, self.filter_condition)
                logging.info(f"应用筛选条件后数据量: {len(df)}条")
            
            # 检查是否有投诉编号列
            if '投诉编号' not in df.columns:
                logging.error("原始数据中没有找到'投诉编号'列，无法排除已抽样数据")
                return None
            
            original_count = len(df)
            logging.info(f"筛选后数据总量: {original_count}条")
            
            # 获取已抽样的投诉编号（使用缓存）
            sampled_complaint_ids = self.get_existing_complaint_ids()
            
            # 排除已抽样数据
            if sampled_complaint_ids:
                remaining_df = df[~df['投诉编号'].astype(str).isin(sampled_complaint_ids)]
                logging.info(f"排除已抽样数据: {len(sampled_complaint_ids)}条")
                logging.info(f"排除后剩余数据: {len(remaining_df)}条")
            else:
                remaining_df = df
                logging.info("没有找到已抽样数据，使用全部筛选后数据")
            
            # 根据投诉内容去重
            remaining_df = self.remove_duplicates_by_content(remaining_df, '投诉内容')
            
            return remaining_df
            
        except Exception as e:
            logging.error(f"获取可用数据失败: {e}")
            return None
    
    def create_sample(self, sample_size, random_state=42, stratify_column=None):
        """创建样本 - 排除已抽样数据并删除重复值"""
        logging.info(f"创建样本: {sample_size}条")
        
        try:
            # 获取可用数据（已应用筛选条件、排除已抽样数据并去重）
            available_df = self.get_available_data()
            
            if available_df is None:
                logging.error("无法获取可用数据")
                return None
            
            # 检查可用数据是否足够
            available_count = len(available_df)
            if available_count <= 0:
                logging.error("没有可用的数据了！")
                return None
            
            if available_count < sample_size:
                logging.warning(f"可用数据只有 {available_count} 条，小于请求的 {sample_size} 条")
                sample_size = available_count
            
            # 分层抽样或简单随机抽样
            if available_count <= sample_size:
                sampled_df = available_df.copy()
                logging.info("可用数据量小于等于样本量，使用全部可用数据")
            else:
                if stratify_column and stratify_column in available_df.columns:
                    # 分层抽样
                    sampled_df, _ = train_test_split(
                        available_df, 
                        train_size=sample_size, 
                        random_state=random_state, 
                        stratify=available_df[stratify_column]
                    )
                    logging.info(f"使用分层抽样，分层列: {stratify_column}")
                else:
                    # 简单随机抽样
                    sampled_df = available_df.sample(n=sample_size, random_state=random_state, replace=False)
                    logging.info("使用简单随机抽样")
            
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"样本_{sample_size}条_{timestamp}.xlsx"
            
            # 保存样本（Excel格式）
            sampled_df.to_excel(output_file, index=False, engine='openpyxl')
            
            # 更新状态 - 确保状态中有 sampled_complaint_ids 键
            if 'sampled_complaint_ids' not in self.status:
                self.status['sampled_complaint_ids'] = []
                
            if '投诉编号' in sampled_df.columns:
                new_complaint_ids = sampled_df['投诉编号'].astype(str).tolist()
                self.status['sampled_complaint_ids'].extend(new_complaint_ids)
                # 去重
                self.status['sampled_complaint_ids'] = list(set(self.status['sampled_complaint_ids']))
            
            # 确保状态中有 generated_files 键
            if 'generated_files' not in self.status:
                self.status['generated_files'] = []
                
            file_info = {
                'filename': output_file.name,
                'size': sample_size,
                'created_time': datetime.now().isoformat(),
                'sampled_complaint_ids': new_complaint_ids if '投诉编号' in sampled_df.columns else []
            }
            self.status['generated_files'].append(file_info)
            
            self._save_status()
            
            # 使缓存失效，强制下次重新扫描
            self.cache_valid = False
            
            logging.info(f"样本保存: {output_file}")
            logging.info(f"样本大小: {sample_size}条")
            return output_file
            
        except Exception as e:
            logging.error(f"创建样本失败: {e}")
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
    
    def get_sampling_status(self):
        """获取抽样状态（考虑筛选条件和去重后的数据）"""
        # 获取可用数据（已应用筛选条件、排除已抽样数据并去重）
        available_df = self.get_available_data()
        
        if available_df is None:
            return None
        
        # 获取已抽样的投诉编号（使用缓存）
        sampled_complaint_ids = self.get_existing_complaint_ids()
        
        status = {
            'total_records': len(available_df) + len(sampled_complaint_ids),
            'sampled_records': len(sampled_complaint_ids),
            'available_records': len(available_df),
            'duplicates_removed': True,
            'filter_applied': self.filter_condition is not None
        }
        
        return status
    
    def rescan_files(self):
        """强制重新扫描所有文件"""
        logging.info("强制重新扫描所有样本文件...")
        self.cache_valid = False
        complaint_ids = self.get_existing_complaint_ids(force_rescan=True)
        self.status['sampled_complaint_ids'] = complaint_ids
        self._save_status()
        logging.info(f"重新扫描完成: 找到 {len(complaint_ids)} 个已抽样投诉编号")
        return len(complaint_ids)

# 主程序
if __name__ == "__main__":
    # 配置文件路径和参数 - 更新为你指定的路径
    INPUT_FILE = "/Users/chenyaxin/Desktop/websitdata/bert/results/是否明示/delete_hostility.csv"
    OUTPUT_DIR = "/Users/chenyaxin/Desktop/审稿修改/分类数据/计算能力"
    
    # 定义筛选条件
    FILTER_CONDITION = {'column': 'prediction', 'value': 1}
    
    try:
        # 创建数据抽样器，传入筛选条件
        sampler = FlexibleDataSampler(INPUT_FILE, OUTPUT_DIR, filter_condition=FILTER_CONDITION)
        
        print("=== 智能数据抽样工具 ===")
        print(f"输入文件: {INPUT_FILE}")
        print(f"输出目录: {OUTPUT_DIR}")
        print(f"筛选条件: {FILTER_CONDITION}")
        
        while True:
            # 显示当前状态
            status = sampler.get_sampling_status()
            if status is None:
                logging.error("无法获取抽样状态")
                exit(1)
                
            print(f"\n=== 当前抽样状态（已应用筛选条件和去重）===")
            print(f"筛选后数据总量: {status['total_records']}")
            print(f"已抽样: {status['sampled_records']}")
            print(f"可用数据（去重后）: {status['available_records']}")
            
            # 显示菜单
            print(f"\n请选择操作:")
            print("1. 创建新样本")
            print("2. 重新扫描文件")
            print("3. 退出")
            
            choice = input("请输入选择 (1-3): ").strip()
            
            if choice == "1":
                # 创建新样本
                if status['available_records'] <= 0:
                    logging.info("所有数据都已抽样完毕！")
                    continue
                    
                print(f"\n=== 创建新样本 ===")
                print(f"可用数据（去重后）: {status['available_records']}条")
                
                try:
                    sample_size = int(input(f"请输入样本大小 (1-{status['available_records']}): "))
                    
                    if sample_size <= 0:
                        print("样本大小必须大于0")
                        continue
                    
                    if sample_size > status['available_records']:
                        print(f"样本大小不能超过剩余数据量 {status['available_records']}")
                        continue
                    
                    # 创建样本 - 不再需要传递筛选条件，因为已在初始化时设置
                    logging.info(f"创建样本，大小: {sample_size}条")
                    output_file = sampler.create_sample(
                        sample_size=sample_size,
                        random_state=42
                    )
                    
                    if output_file is not None:
                        print(f"\n✅ 样本创建成功!")
                        print(f"📊 文件: {output_file.name}")
                        print(f"📈 大小: {sample_size}条")
                        
                        # 显示新的状态
                        new_status = sampler.get_sampling_status()
                        if new_status:
                            print(f"📋 新状态: 已使用 {new_status['sampled_records']}/{new_status['total_records']}")
                            print(f"🔄 剩余可用数据（去重后）: {new_status['available_records']}条")
                    else:
                        print("❌ 样本创建失败!")
                        
                except ValueError:
                    print("请输入有效的数字")
                except Exception as e:
                    print(f"创建样本失败: {e}")
            
            elif choice == "2":
                # 重新扫描文件
                count = sampler.rescan_files()
                print(f"重新扫描完成，找到 {count} 个已抽样投诉编号")
            
            elif choice == "3":
                # 退出
                print("程序结束")
                break
            
            else:
                print("无效选择，请重新输入")
        
    except Exception as e:
        print(f"程序运行失败: {e}")
        import traceback
        traceback.print_exc()