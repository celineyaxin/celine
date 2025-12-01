import pandas as pd
from openai import OpenAI
import time
import logging
import os
import json
from datetime import datetime
import re

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FinancialVulnerabilityClassifier:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        
        # 分类结果映射
        self.vulnerability_mapping = {
            "是": 1,  # 计算能力不足
            "否": 0,  # 计算能力正常
            "不确定": 2,
            "非金融相关": 3
        }
        
        # 专注于计算能力判断的prompt
        self.prompt_template = """请作为金融行为分析专家，仔细分析以下消费者投诉文本，判断该消费者是否表现出计算能力不足的特征。

## 计算能力不足的定义与判断标准

### 核心定义
计算能力不足指消费者在理解或计算贷款利率方面存在数学技能上的困难，即使他们可能没有直接使用"不会算"等词语。

### 具体表现特征（包括但不限于）

1. **直接表达计算困惑**：
   - 明确表示不理解计算过程或结果
   - 抱怨数字、利率或费用计算太复杂
   - 表示需要他人帮助才能理解计算

2. **展示错误的理解或计算**：
   - 对利率概念理解有误（如混淆不同期限利率）
   - 使用不正确的计算方法
   - 对还款计划或费用结构理解混乱

3. **间接表现计算困难**：
   - 对数字信息感到困惑或回避
   - 无法解释清楚自己的计算困惑
   - 表现出对金融计算的焦虑或不自信

### 判断原则
请基于文本的整体语义进行判断，而不仅仅依赖特定关键词。重点分析消费者是否真正理解或能够处理相关的计算问题。

## 分析任务

请分析以下投诉文本，判断消费者是否存在计算能力不足：

**投诉文本**："{complaint_text}"

请严格按照以下JSON格式输出结果：
{{
  "calculation_ability_deficient": "是/否/不确定/非金融相关",
  "reasoning": "详细分析文本语义，说明判断依据，重点分析消费者对计算问题的理解和处理能力"
}}
"""

    def classify_single_complaint(self, complaint_text, max_retries=3):
        """对单个投诉文本进行计算能力分类"""
        for attempt in range(max_retries):
            try:
                if not complaint_text or len(complaint_text.strip()) < 5:
                    return self._create_default_result("Skip", "投诉内容过短或为空")
                
                prompt = self.prompt_template.format(complaint_text=complaint_text)
                
                response = self.client.chat.completions.create(
                    model="Qwen/Qwen2.5-72B-Instruct",
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1,
                    max_tokens=400
                )
                
                result_text = response.choices[0].message.content.strip()
                logging.info(f"API响应: {result_text}")
                
                # 解析JSON响应
                parsed_result = self._parse_json_response(result_text)
                if parsed_result:
                    return parsed_result
                else:
                    logging.warning(f"第{attempt+1}次未能解析JSON响应，尝试文本解析: {result_text}")
                    # 如果JSON解析失败，尝试文本解析
                    parsed_result = self._parse_text_response(result_text)
                    if parsed_result:
                        return parsed_result
                    
            except Exception as e:
                logging.error(f"第{attempt+1}次分类失败: {str(e)}")
            
            if attempt < max_retries - 1:
                time.sleep(2)
        
        # 所有重试都失败
        return self._create_error_result(f"经过{max_retries}次重试后仍失败")
    
    def _parse_json_response(self, response_text):
        """解析JSON格式的响应"""
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                
                # 验证必要字段
                if "calculation_ability_deficient" in result:
                    vulnerability_status = result["calculation_ability_deficient"]
                    category_id = self.vulnerability_mapping.get(vulnerability_status, 2)  # 默认为不确定
                    
                    reasoning = result.get("reasoning", "基于文本语义的分析")
                    
                    return {
                        "category_id": category_id,
                        "category_name": vulnerability_status,
                        "confidence": "中",  # 简化处理，不再从API获取置信度
                        "reasoning": reasoning,
                        "strong_dimensions": [],
                        "weak_dimensions": []
                    }
        except json.JSONDecodeError as e:
            logging.warning(f"JSON解析错误: {e}")
        except Exception as e:
            logging.warning(f"JSON响应处理错误: {e}")
        
        return None
    
    def _parse_text_response(self, response_text):
        """解析文本格式的响应（备选方案）"""
        try:
            # 提取分类结果
            patterns = [
                r'calculation_ability_deficient[": ]+([^",}\n]+)',
                r'计算能力[不足]?[：:]\s*([^\n]+)',
                r'is_innumeracy[": ]+([^",}\n]+)',
            ]
            
            vulnerability_status = None
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    vulnerability_status = match.group(1).strip()
                    break
            
            if not vulnerability_status:
                # 直接搜索关键词
                for status in ["是", "否", "不确定", "非金融相关"]:
                    if status in response_text:
                        vulnerability_status = status
                        break
            
            # 提取判断理由
            reasoning = ""
            reasoning_patterns = [
                r'reasoning[": ]+([^",}\n]+)',
                r'理由[：:]\s*([^\n]+)',
                r'分析[：:]\s*([^\n]+)'
            ]
            for pattern in reasoning_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    reasoning = match.group(1).strip()
                    break
            
            if not reasoning:
                # 如果找不到明确的理由，使用默认值
                reasoning = "基于投诉内容的语义分析"
            
            if vulnerability_status:
                category_id = self.vulnerability_mapping.get(vulnerability_status, 2)
                return {
                    "category_id": category_id,
                    "category_name": vulnerability_status,
                    "confidence": "中",
                    "reasoning": reasoning,
                    "strong_dimensions": [],
                    "weak_dimensions": []
                }
                
        except Exception as e:
            logging.warning(f"文本响应解析错误: {e}")
        
        return None
    
    def _create_default_result(self, category_name, reasoning):
        """创建默认结果"""
        return {
            "category_id": 0,
            "category_name": category_name,
            "confidence": "高",
            "reasoning": reasoning,
            "strong_dimensions": [],
            "weak_dimensions": []
        }
    
    def _create_error_result(self, error_message):
        """创建错误结果"""
        return {
            "category_id": -1,
            "category_name": "Error",
            "confidence": "低",
            "reasoning": error_message,
            "strong_dimensions": [],
            "weak_dimensions": []
        }

    def classify_complaints(self, input_file, output_file=None, 
                          text_column='complaint_content', sample_size=None,
                          max_retries=3, save_batch_size=20, delay=2,
                          resume_from_checkpoint=True):
        """
        分类投诉内容，支持灵活样本数量和简化的断点续跑
        """
        try:
            # 设置输出文件
            if output_file is None:
                base_name = os.path.splitext(input_file)[0]
                if sample_size:
                    output_file = f"{base_name}_计算能力分类_前{sample_size}条.xlsx"
                else:
                    output_file = f"{base_name}_计算能力分类_全部.xlsx"
            
            # 读取原始数据
            logging.info(f"正在读取原始数据文件: {input_file}")
            original_df = pd.read_excel(input_file)
            
            # 应用样本大小限制
            total_records = len(original_df)
            if sample_size is not None:
                if total_records > sample_size:
                    original_df = original_df.head(sample_size)
                    total_records = sample_size
                    logging.info(f"将处理前 {sample_size} 条记录")
                else:
                    logging.warning(f"数据文件只有 {total_records} 条记录，将处理全部数据")
            else:
                logging.info(f"将处理全部 {total_records} 条记录")
            
            # 检查必要的列
            if text_column not in original_df.columns:
                # 尝试找到包含"投诉"或"内容"的列
                complaint_columns = [col for col in original_df.columns if '投诉' in col or '内容' in col or 'content' in col.lower()]
                if complaint_columns:
                    text_column = complaint_columns[0]
                    logging.info(f"自动选择列: {text_column}")
                else:
                    raise ValueError(f"输入文件中必须包含投诉内容列，当前列名: {original_df.columns.tolist()}")
            
            # 断点续跑逻辑
            df = None
            if resume_from_checkpoint and os.path.exists(output_file):
                try:
                    existing_df = pd.read_excel(output_file)
                    
                    # 验证恢复文件
                    required_columns = ['category_id', 'category_name', 'confidence', 
                                      'reasoning', 'strong_dimensions', 'weak_dimensions']
                    
                    if len(existing_df) == len(original_df) and \
                       all(col in existing_df.columns for col in required_columns):
                        
                        df = existing_df
                        processed_count = len(df[~df['category_id'].isin([-2, -1])])
                        logging.info(f"从最终文件恢复: 已处理 {processed_count}/{total_records} 条记录")
                    else:
                        logging.warning("最终文件验证失败，将重新开始处理")
                        df = None
                except Exception as e:
                    logging.warning(f"读取最终文件失败: {e}")
                    df = None
            
            # 初始化新处理
            if df is None:
                df = original_df.copy()
                # 新增计算能力分类相关列
                df['category_id'] = -2  # -2 表示未处理
                df['category_name'] = ''
                df['confidence'] = ''
                df['reasoning'] = ''
                df['strong_dimensions'] = ''
                df['weak_dimensions'] = ''
                df['strong_dimensions_count'] = 0
                df['weak_dimensions_count'] = 0
                
                logging.info("开始新处理")
                
                # 创建输入文件的备份
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = input_file.replace('.xlsx', f'_backup_{timestamp}.xlsx')
                df.to_excel(backup_file, index=False)
                logging.info(f"已创建备份文件: {backup_file}")
            
            # 找出需要处理的记录
            unprocessed_indices = df[df['category_id'].isin([-2, -1])].index.tolist()
            
            if not unprocessed_indices:
                logging.info("所有记录都已处理完成！")
                self._print_classification_statistics(df)
                return df
            
            total_to_process = len(unprocessed_indices)
            processed_count = len(df) - total_to_process
            
            logging.info(f"开始处理 {total_to_process} 条未完成记录")
            
            try:
                for i, idx in enumerate(unprocessed_indices):
                    complaint_text = str(df.at[idx, text_column]).strip()
                    
                    # 检查内容是否为空
                    if not complaint_text or complaint_text == 'nan':
                        default_result = self._create_default_result("Skip", "投诉内容为空")
                        self._update_dataframe_row(df, idx, default_result)
                        processed_count += 1
                        continue
                    
                    # 分类处理
                    current_total = processed_count + i + 1
                    logging.info(f"处理第 {i+1}/{total_to_process} 条记录 (总进度: {current_total}/{len(df)})")
                    
                    result = self.classify_single_complaint(complaint_text, max_retries=max_retries)
                    
                    # 更新结果
                    self._update_dataframe_row(df, idx, result)
                    
                    # 进度提示
                    if (i + 1) % 5 == 0:
                        success_count = len(df[df['category_id'].isin([0, 1, 2, 3])])
                        print(f"进度: {current_total}/{len(df)}，成功分类: {success_count} 条")
                    
                    # 分批保存到最终文件
                    if (i + 1) % save_batch_size == 0:
                        df.to_excel(output_file, index=False)
                        logging.info(f"进度已保存至: {output_file} (已处理 {current_total}/{len(df)} 条)")
                    
                    # 延迟以避免API限制
                    time.sleep(delay)
                
                # 处理完成，保存最终结果
                df.to_excel(output_file, index=False)
                logging.info(f"处理完成，最终结果已保存至: {output_file}")
                
                # 输出统计信息
                self._print_classification_statistics(df)
                
                logging.info("计算能力分类完成！")
                
            except KeyboardInterrupt:
                logging.info("程序被用户中断，保存当前进度...")
                # 保存当前进度到最终文件
                df.to_excel(output_file, index=False)
                logging.info(f"中断时的进度已保存至: {output_file}")
                logging.info(f"已处理 {processed_count + i + 1}/{len(df)} 条记录")
                logging.info("下次运行时会自动从断点继续")
                raise
                
            except Exception as e:
                logging.error(f"处理过程中出错: {e}")
                # 保存当前进度到最终文件
                df.to_excel(output_file, index=False)
                logging.info(f"出错时的进度已保存至: {output_file}")
                logging.info("下次运行时会自动从断点继续")
                raise
            
            return df
            
        except Exception as e:
            logging.error(f"分类失败: {e}")
            raise
    
    def _update_dataframe_row(self, df, idx, result):
        """更新DataFrame行数据"""
        df.at[idx, 'category_id'] = int(result['category_id'])
        df.at[idx, 'category_name'] = str(result['category_name'])
        df.at[idx, 'confidence'] = str(result.get('confidence', ''))
        df.at[idx, 'reasoning'] = str(result.get('reasoning', ''))
        
        # 处理strong_dimensions
        strong_dimensions = result.get('strong_dimensions', [])
        if isinstance(strong_dimensions, list):
            df.at[idx, 'strong_dimensions'] = ';'.join(strong_dimensions)
            # 统计强维度数量
            df.at[idx, 'strong_dimensions_count'] = len(strong_dimensions)
        else:
            df.at[idx, 'strong_dimensions'] = str(strong_dimensions)
            df.at[idx, 'strong_dimensions_count'] = 0
                
        # 处理weak_dimensions
        weak_dimensions = result.get('weak_dimensions', [])
        if isinstance(weak_dimensions, list):
            df.at[idx, 'weak_dimensions'] = ';'.join(weak_dimensions)
            # 统计弱维度数量
            df.at[idx, 'weak_dimensions_count'] = len(weak_dimensions)
        else:
            df.at[idx, 'weak_dimensions'] = str(weak_dimensions)
            df.at[idx, 'weak_dimensions_count'] = 0
    
    def _print_classification_statistics(self, df):
        """打印分类统计信息"""
        category_names = {
            1: "是(计算能力不足)",
            0: "否(计算能力正常)", 
            2: "不确定",
            3: "非金融相关",
            -1: "Error",
            -2: "未处理"
        }
        
        stats = df['category_id'].value_counts().sort_index()
        print("\n" + "="*50)
        print("计算能力分类统计结果")
        print("="*50)
        
        total_records = len(df)
        for category_id, count in stats.items():
            category_name = category_names.get(category_id, f"未知({category_id})")
            percentage = (count / total_records) * 100
            print(f"{category_id}. {category_name}: {count} 条 ({percentage:.1f}%)")
        
        # 计算关键指标
        innumeracy_count = len(df[df['category_id'] == 1])
        normal_count = len(df[df['category_id'] == 0])
        uncertain_count = len(df[df['category_id'] == 2])
        non_financial_count = len(df[df['category_id'] == 3])
        error_count = len(df[df['category_id'] == -1])
        unprocessed_count = len(df[df['category_id'] == -2])
        
        financial_related_count = innumeracy_count + normal_count + uncertain_count
        
        print("\n" + "="*50)
        print("关键指标汇总")
        print("="*50)
        print(f"总记录数: {total_records}")
        print(f"金融相关投诉: {financial_related_count} 条 ({(financial_related_count/total_records)*100:.1f}%)")
        print(f"├─ 计算能力不足: {innumeracy_count} 条 ({(innumeracy_count/total_records)*100:.1f}%)")
        print(f"├─ 计算能力正常: {normal_count} 条 ({(normal_count/total_records)*100:.1f}%)")
        print(f"└─ 不确定: {uncertain_count} 条 ({(uncertain_count/total_records)*100:.1f}%)")
        print(f"非金融相关投诉: {non_financial_count} 条 ({(non_financial_count/total_records)*100:.1f}%)")
        
        if financial_related_count > 0:
            innumeracy_rate = (innumeracy_count / financial_related_count) * 100
            print(f"\n金融相关投诉中计算能力不足比例: {innumeracy_rate:.1f}%")

def main():
    """主函数 - 直接运行即可"""
    
    # ========== 配置区域 ==========
    
    # 1. 设置您的API密钥
    API_KEY = "sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol"
    
    # 2. 设置输入文件路径
    input_file = "/Users/chenyaxin/Desktop/审稿修改/分类数据/计算能力/明示投诉_prediction1_一级样本_10000条_from0_size1000_filter_prediction_1.xlsx"
    
    # 3. 设置处理参数
    sample_size = 1000  # 处理前多少条数据，设为None则处理全部
    max_retries = 3    # 最大重试次数
    save_batch_size = 10  # 每处理多少条保存一次
    delay = 2          # API调用间隔（秒）
    
    # 4. 设置文本列名
    text_column = "投诉内容"
    
    # ========== 执行区域 ==========
    
    try:
        # 创建分类器实例
        classifier = FinancialVulnerabilityClassifier(API_KEY)
        
        # 开始分类
        result_df = classifier.classify_complaints(
            input_file=input_file,
            text_column=text_column,
            sample_size=sample_size,
            max_retries=max_retries,
            save_batch_size=save_batch_size,
            delay=delay,
            resume_from_checkpoint=True
        )
        
        print("\n" + "="*60)
        print("计算能力不足分类任务完成！")
        print("="*60)
        
        # 显示结果文件路径
        output_file = input_file.replace('.xlsx', f'_计算能力分类_前{sample_size}条.xlsx') if sample_size else input_file.replace('.xlsx', '_计算能力分类_全部.xlsx')
        print(f"结果已保存至: {output_file}")
        
    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{input_file}'")
        print("请检查文件路径是否正确")
    except Exception as e:
        print(f"分类过程中出错: {e}")
        print("请检查API密钥和网络连接")

if __name__ == "__main__":
    main()