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

class RepresentativenessBiasClassifier:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        
        # 代表性偏差结果映射
        self.bias_mapping = {
            "是": 1,  # 存在代表性偏差
            "否": 0,  # 不存在代表性偏差
            "不确定": 2
        }
        
        # 代表性偏差类型映射
        self.bias_type_mapping = {
            "表面特征判断": "surface_feature",
            "过度依赖经验": "over_reliance_experience", 
            "忽视基础概率": "ignore_base_rate",
            "典型性思维": "typicality_thinking"
        }
        
        # 代表性偏差检测prompt
        self.prompt_template = """请作为行为金融学专家，严格依据审稿人要求的三个核心特征分析消费者投诉中的代表性偏差：

**代表性偏差必须体现以下至少一个核心特征**：

1. **忽略统计基础率**
   - 决策时忽视行业基础概率、普遍统计数据
   - 证据："相信零风险高收益"，忽视此类承诺的普遍虚假性
   - 证据："觉得大平台不会出事"，忽视行业风险概率

2. **基于相似性而非概率判断**
   - 依赖表面特征相似性而非概率分析
   - 证据："因为看起来像银行/正规机构就信任"
   - 证据："界面专业、广告多就觉得可靠"

3. **小样本过度推断**
   - 从个别案例或有限经验推断普遍规律
   - 证据："朋友赚钱了所以我也能赚"
   - 证据："之前几次成功所以这次也会成功"

### 严格判断标准

**是（存在代表性偏差）**：
- 必须明确体现上述至少一个核心特征
- 有具体文本证据显示决策基于典型性而非概率
- 显示消费者忽视了基础统计信息

**否（不存在代表性偏差）**：
- 决策基于具体信息分析或比较
- 考虑了统计概率或风险信息
- 问题发生在理性评估之后

**不确定**：
- 文本信息不足，无法判断决策依据
- 仅描述结果，未提及决策过程
- 仅表达情绪或财务困难，无决策过程描述

### 符合审稿要求的示例

**存在代表性偏差**：
- "看到央视广告就觉得靠谱，把积蓄都投了" → 基于相似性判断
- "朋友在这个平台赚了钱，我觉得我也能赚" → 小样本推断
- "相信零风险高收益承诺，没想太多就投了" → 忽视基础概率
- "因为是大公司旗下产品，觉得肯定安全，没仔细看条款" → 基于表面特征

**不存在代表性偏差**：
- "比较了多家平台利率后选择，但实际费用更高"
- "根据信用评分申请贷款，但利率不透明"
- "阅读合同后发现隐藏条款"
- "计算了年化利率发现高于法定标准"

### 特别注意
- 仅表达后悔或描述损失不等于代表性偏差
- 必须有证据显示决策机制存在认知偏差
- 严格区分"受害"与"因认知偏差决策"
- 催收相关投诉通常不体现代表性偏差，除非显示决策时的认知过程

请严格按照以下JSON格式输出：
{{
"has_representativeness_bias": "是/否/不确定",
"confidence": "高/中/低", 
"reasoning": "基于三个核心特征的判断理由",
"bias_evidence": ["具体的文本证据"],
"bias_type": ["忽略基础概率"/"相似性判断"/"小样本推断"]
}}

投诉内容：
"{complaint_text}"
"""
       
    def classify_single_complaint(self, complaint_text, max_retries=3):
        """对单个投诉文本进行代表性偏差检测"""
        for attempt in range(max_retries):
            try:
                if not complaint_text or len(complaint_text.strip()) < 5:
                    return self._create_default_result("Skip", "投诉内容过短或为空")
                
                prompt = self.prompt_template.format(complaint_text=complaint_text)
                
                response = self.client.chat.completions.create(
                    model="Qwen/QwQ-32B",   
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.0,  # 设置为0确保结果一致性
                    max_tokens=800
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
                if "has_representativeness_bias" in result:
                    bias_status = result["has_representativeness_bias"]
                    bias_id = self.bias_mapping.get(bias_status, 2)  # 默认为不确定
                    
                    # 处理reasoning字段
                    reasoning = result.get("reasoning", "基于代表性偏差核心特征的综合评估")
                    
                    # 获取偏差证据和类型
                    bias_evidence = result.get("bias_evidence", [])
                    bias_type = result.get("bias_type", [])
                    
                    return {
                        "bias_id": bias_id,
                        "bias_status": bias_status,
                        "confidence": result.get("confidence", "中"),
                        "reasoning": reasoning,
                        "bias_evidence": bias_evidence,
                        "bias_type": bias_type
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
                r'has_representativeness_bias[": ]+([^",}\n]+)',
                r'代表性偏差[：:]\s*([^\n]+)',
                r'bias[": ]+([^",}\n]+)',
                r'是否[：:]\s*([^\n]+)'
            ]
            
            bias_status = None
            for pattern in patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    bias_status = match.group(1).strip()
                    break
            
            if not bias_status:
                # 直接搜索关键词
                for status in ["是", "否", "不确定"]:
                    if status in response_text:
                        bias_status = status
                        break
            
            # 提取置信度
            confidence = "中"
            confidence_patterns = [
                r'confidence[": ]+([^",}\n]+)',
                r'置信度[：:]\s*([^\n]+)'
            ]
            for pattern in confidence_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    conf = match.group(1).strip()
                    if conf in ["高", "中", "低"]:
                        confidence = conf
                    break
            
            # 提取判断理由
            reasoning = ""
            reasoning_patterns = [
                r'reasoning[": ]+([^",}\n]+)',
                r'判断理由[：:]\s*([^\n]+)',
                r'理由[：:]\s*([^\n]+)'
            ]
            for pattern in reasoning_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    reasoning = match.group(1).strip()
                    break
            
            if not reasoning:
                # 如果找不到明确的理由，从文本中提取关键信息
                if "广告" in response_text or "看起来" in response_text or "表面" in response_text:
                    reasoning = "基于表面特征判断"
                elif "朋友" in response_text or "经验" in response_text or "之前" in response_text:
                    reasoning = "基于小样本推断"
                elif "零风险" in response_text or "高收益" in response_text or "肯定" in response_text:
                    reasoning = "忽视基础概率"
                else:
                    reasoning = "基于投诉内容的综合评估"
            
            # 文本解析中不再尝试提取详细证据和类型
            bias_evidence = []
            bias_type = []
            
            if bias_status:
                bias_id = self.bias_mapping.get(bias_status, 2)
                return {
                    "bias_id": bias_id,
                    "bias_status": bias_status,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "bias_evidence": bias_evidence,
                    "bias_type": bias_type
                }
                
        except Exception as e:
            logging.warning(f"文本响应解析错误: {e}")
        
        return None
    
    def _create_default_result(self, bias_status, reasoning):
        """创建默认结果"""
        return {
            "bias_id": 0,
            "bias_status": bias_status,
            "confidence": "高",
            "reasoning": reasoning,
            "bias_evidence": [],
            "bias_type": []
        }
    
    def _create_error_result(self, error_message):
        """创建错误结果"""
        return {
            "bias_id": -1,
            "bias_status": "Error",
            "confidence": "低",
            "reasoning": error_message,
            "bias_evidence": [],
            "bias_type": []
        }

    def classify_complaints(self, input_file, output_file=None, 
                          text_column='complaint_content', sample_size=None,
                          max_retries=3, save_batch_size=20, delay=2,
                          resume_from_checkpoint=True):
        """
        检测投诉内容中的代表性偏差，支持灵活样本数量和简化的断点续跑
        """
        try:
            # 设置输出文件
            if output_file is None:
                base_name = os.path.splitext(input_file)[0]
                if sample_size:
                    output_file = f"{base_name}_代表性偏差检测_前{sample_size}条.xlsx"
                else:
                    output_file = f"{base_name}_代表性偏差检测_全部.xlsx"
            
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
                    required_columns = ['bias_id', 'bias_status', 'confidence', 
                                      'reasoning', 'bias_evidence', 'bias_type']
                    
                    if len(existing_df) == len(original_df) and \
                       all(col in existing_df.columns for col in required_columns):
                        
                        df = existing_df
                        processed_count = len(df[~df['bias_id'].isin([-2, -1])])
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
                # 新增代表性偏差检测相关列
                df['bias_id'] = -2  # -2 表示未处理
                df['bias_status'] = ''
                df['confidence'] = ''
                df['reasoning'] = ''
                df['bias_evidence'] = ''
                df['bias_type'] = ''
                
                logging.info("开始新处理")
                
                # 创建输入文件的备份
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = input_file.replace('.xlsx', f'_backup_{timestamp}.xlsx')
                df.to_excel(backup_file, index=False)
                logging.info(f"已创建备份文件: {backup_file}")
            
            # 找出需要处理的记录
            unprocessed_indices = df[df['bias_id'].isin([-2, -1])].index.tolist()
            
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
                        success_count = len(df[df['bias_id'].isin([0, 1, 2])])
                        print(f"进度: {current_total}/{len(df)}，成功检测: {success_count} 条")
                    
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
                
                logging.info("代表性偏差检测完成！")
                
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
            logging.error(f"检测失败: {e}")
            raise
    
    def _update_dataframe_row(self, df, idx, result):
        """更新DataFrame行数据"""
        df.at[idx, 'bias_id'] = int(result['bias_id'])
        df.at[idx, 'bias_status'] = str(result['bias_status'])
        df.at[idx, 'confidence'] = str(result.get('confidence', ''))
        df.at[idx, 'reasoning'] = str(result.get('reasoning', ''))
        
        # 处理bias_evidence
        bias_evidence = result.get('bias_evidence', [])
        if isinstance(bias_evidence, list):
            df.at[idx, 'bias_evidence'] = ';'.join(bias_evidence)
        else:
            df.at[idx, 'bias_evidence'] = str(bias_evidence)
                
        # 处理bias_type
        bias_type = result.get('bias_type', [])
        if isinstance(bias_type, list):
            df.at[idx, 'bias_type'] = ';'.join(bias_type)
        else:
            df.at[idx, 'bias_type'] = str(bias_type)
            
    def _print_classification_statistics(self, df):
        """打印检测统计信息"""
        bias_names = {
            1: "是(存在偏差)",
            0: "否(不存在偏差)", 
            2: "不确定",
            -1: "Error",
            -2: "未处理"
        }
        
        stats = df['bias_id'].value_counts().sort_index()
        print("\n" + "="*50)
        print("代表性偏差检测统计结果")
        print("="*50)
        
        total_records = len(df)
        for bias_id, count in stats.items():
            bias_name = bias_names.get(bias_id, f"未知({bias_id})")
            percentage = (count / total_records) * 100
            print(f"{bias_id}. {bias_name}: {count} 条 ({percentage:.1f}%)")
        
        # 计算关键指标
        has_bias_count = len(df[df['bias_id'] == 1])
        no_bias_count = len(df[df['bias_id'] == 0])
        uncertain_count = len(df[df['bias_id'] == 2])
        error_count = len(df[df['bias_id'] == -1])
        unprocessed_count = len(df[df['bias_id'] == -2])
        
        print("\n" + "="*50)
        print("关键指标汇总")
        print("="*50)
        print(f"总记录数: {total_records}")
        print(f"存在代表性偏差: {has_bias_count} 条 ({(has_bias_count/total_records)*100:.1f}%)")
        print(f"不存在代表性偏差: {no_bias_count} 条 ({(no_bias_count/total_records)*100:.1f}%)")
        print(f"不确定: {uncertain_count} 条 ({(uncertain_count/total_records)*100:.1f}%)")
        
        # 输出代表性偏差类型分布
        if 'bias_type' in df.columns:
            bias_type_stats = {}
            for types in df['bias_type']:
                if types and isinstance(types, str):
                    for bias_type in types.split(';'):
                        if bias_type:
                            bias_type_stats[bias_type] = bias_type_stats.get(bias_type, 0) + 1
            
            if bias_type_stats:
                print(f"\n代表性偏差类型分布:")
                for bias_type, count in sorted(bias_type_stats.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / has_bias_count) * 100 if has_bias_count > 0 else 0
                    print(f"  {bias_type}: {count} 次提及 ({percentage:.1f}%的存在偏差案例)")

def main():
    """主函数 - 直接运行即可"""
    
    # ========== 配置区域 ==========
    
    # 1. 设置您的API密钥
    API_KEY = "sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol"
    
    # 2. 设置输入文件路径
    input_file = "/Users/chenyaxin/Desktop/审稿修改/分类数据/计算能力/明示投诉_prediction1_一级样本_10000条_from9000_size1000_filter_prediction_1.xlsx"
    
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
        classifier = RepresentativenessBiasClassifier(API_KEY)
        
        # 开始检测
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
        print("代表性偏差检测任务完成！")
        print("="*60)
        
        # 显示结果文件路径
        output_file = input_file.replace('.xlsx', f'_代表性偏差检测_前{sample_size}条.xlsx') if sample_size else input_file.replace('.xlsx', '_代表性偏差检测_全部.xlsx')
        print(f"结果已保存至: {output_file}")
        
    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{input_file}'")
        print("请检查文件路径是否正确")
    except Exception as e:
        print(f"检测过程中出错: {e}")
        print("请检查API密钥和网络连接")

if __name__ == "__main__":
    main()