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
        
        # 简化的分类结果映射
        self.vulnerability_mapping = {
            "是": 1,  # 金融素养弱势群体
            "否": 0,  # 非金融素养弱势群体
            "不确定": 2,
            "非金融相关": 3  # 新增：非金融相关投诉
        }
        
        # 维度映射
        self.dimension_mapping = {
            "financial_concept": "金融概念理解",
            "financial_decision": "金融决策能力", 
            "financial_rights": "金融权益认知"
        }
        
        # 更新后的prompt模板
        self.prompt_template = """请作为金融行为分析专家，基于消费者投诉文本，判断该消费者是否属于金融素养弱势群体。

**核心定义**：金融素养弱势群体指在金融知识、概念理解或决策能力方面存在系统性且明显的不足，导致其无法做出理性金融决策或保护自身权益的消费者。仅表达不满或遇到财务困难但未体现认知缺陷的，不属于弱势群体。

### 重要区分原则
- **识别问题 ≠ 素养不足**：能够识别不公平条款、隐藏费用或欺诈行为，恰恰证明金融素养较高
- **投诉行为 ≠ 认知缺陷**：主动投诉、询问客服、指出问题属于维权意识强的表现
- **遇到陷阱 ≠ 决策失误**：被金融机构欺骗不等于消费者决策能力差
- **催收投诉 ≠ 维权意识**：仅投诉催收骚扰不等于金融素养高，这可能是对骚扰的自然反应

**判定维度**：

1. **金融概念理解**
   - **不足表现**：明确显示不理解基本金融术语（如年化利率、手续费、违约金），混淆利率类型（如分不清日利率和年利率），或无法理解金融产品的基本机制。
     - 证据："不知道年化利率是什么"、"分不清日利率和年利率"、"不明白手续费是什么"
   - **良好表现**：能准确使用金融术语，理解利率计算或产品机制。
     - 证据："我计算了年化利率是36%"、"他们说的日利率0.05%，但年化很高"

2. **金融决策能力**  
   - **不足表现**：显示缺乏理性借贷决策过程，如未比较产品、未评估还款能力、冲动借款、过度负债。
     - 证据："急需用钱就借了，没看其他家"、"借款时没考虑怎么还"
   - **良好表现**：在借款前比较多家产品，评估自身还款能力，或有财务规划。
     - 证据："我比较了不同平台的利率"、"根据收入选择了合适的产品"

3. **金融权益认知**
   - **不足表现**：不了解消费者基本权利（如知情权、公平交易权），不知道正规维权渠道（如监管机构投诉）。
     - 证据："不知道可以投诉"、"不了解合法利率范围"
   - **良好表现**：了解自身权利，并知道通过合法渠道维权。
     - 证据："我已向银保监会投诉"、"根据合同法要求解释费用"

**是（金融素养弱势群体）**：
- 必须满足以下任一条件：
  - 在2个及以上维度表现明显不足，且有具体文本证据支持（不能仅基于推断）。
  - 在"金融概念理解"维度存在严重缺陷（如完全不懂利率概念），并至少另一维度不足。

**否（非金融素养弱势群体）**：
- 必须同时满足：
  - 在至少一个维度表现良好（如能识别问题、主动维权、理解概念）
  - 文本显示具有明确的金融知识或维权意识证据
  - 没有系统性认知缺陷的证据

**不确定**：
- 满足以下任一条件：
  - 文本信息不足，无法评估至少两个维度
  - 仅描述事实、情绪或财务困难，但未体现明确的认知缺陷或良好表现
  - 证据模糊或矛盾，无法明确判断属于弱势还是非弱势

**非金融相关**：
- 投诉内容与金融产品/服务无关（如纯物流问题、商品质量）。

### 精选判断示例

**金融素养弱势群体投诉示例：**
- "我不懂什么是年利率，他们说什么就是什么。看到广告说借钱容易就点了，现在要还好多钱，根本还不起了，也不知道找谁帮忙。"
- "我借了5000块钱，他们让我还，但我不知道利息怎么算的。我朋友说利息太高了，但我已经签字了，不知道该怎么办。借钱的时候没想那么多，就是急用钱。"
- "他们说日利率很低，我以为很划算就借了，后来才发现一年要还很多。现在逾期了，他们说要上征信，我也不知道征信是什么，就让他们随便处理吧。"

**非金融素养弱势群体投诉示例：**
- "我在某平台借款时，发现他们宣传的年化利率是8%，但合同里隐藏了服务费和保险费，实际年化达到36%。我立即指出了这个问题并要求解释。"
- "我在贷款时被收取了不合理的'征信查询费'，我查询了相关法规发现这是违规收费，已经向银保监会投诉并要求退还。"
- "我计算了这笔贷款的实际年化利率达到48%，远超法定标准。我保留了所有证据，准备通过法律途径解决。"

**不确定示例（特别是催收相关）：**
- "催收人员天天打电话骚扰我，还威胁要上门，严重影响我的生活。"
- "他们不停地给我家人朋友打电话，泄露我的隐私，让我很丢脸。"
- "催收人员态度恶劣，辱骂我，我要求他们停止这种暴力催收行为。"

### 关键原则
- **保护维权意识**：能够识别问题并投诉的消费者通常具有较好金融素养
- **区分受害与无知**：被金融机构欺骗≠金融素养低，被动接受欺骗才可能体现素养低
- **证据优先**：必须有明确文本证据表明认知缺陷，不能基于遭遇推断素养
- **积极表现优先**：任一维度的良好表现都倾向于"否"的判断

**特别注意**：
- 识别"阴阳合同"、"权益服务费实质"、"利率不透明"等行为，证明消费者具有金融概念理解和权益认知
- 主动"询问客服"证明具有维权意识
- 这些行为应作为判断"否"的证据

请严格按照以下JSON格式输出：
{{
"is_vulnerable": "是/否/不确定/非金融相关",
"confidence": "高/中/低",
"reasoning": "简要说明理由，说明判断依据",
"strong_dimensions": ["表现良好的维度"],
"weak_dimensions": ["表现薄弱的维度"]
}}

投诉内容：
"{complaint_text}"
"""
    
    def classify_single_complaint(self, complaint_text, max_retries=3):
        """对单个投诉文本进行金融素养分类"""
        for attempt in range(max_retries):
            try:
                if not complaint_text or len(complaint_text.strip()) < 5:
                    return self._create_default_result("Skip", "投诉内容过短或为空")
                
                prompt = self.prompt_template.format(complaint_text=complaint_text)
                
                response = self.client.chat.completions.create(
                    model="Qwen/QwQ-32B",   
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1,
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
                if "is_vulnerable" in result:
                    vulnerability_status = result["is_vulnerable"]
                    category_id = self.vulnerability_mapping.get(vulnerability_status, 2)  # 默认为不确定
                    
                    # 处理reasoning字段，移除固定开头
                    reasoning = result.get("reasoning", "基于三个维度的综合评估")
                    # 移除固定的开头语句
                    reasoning = reasoning.replace("基于三个维度的详细评估理由，说明判断依据：", "").replace("基于三个维度的详细评估理由，说明判断依据", "").strip()
                    
                    # 获取强维度和弱维度
                    strong_dimensions = result.get("strong_dimensions", [])
                    weak_dimensions = result.get("weak_dimensions", [])
                    
                    return {
                        "category_id": category_id,
                        "category_name": vulnerability_status,
                        "confidence": result.get("confidence", "中"),
                        "reasoning": reasoning,
                        "strong_dimensions": strong_dimensions,
                        "weak_dimensions": weak_dimensions
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
                r'is_vulnerable[": ]+([^",}\n]+)',
                r'金融素养[弱势群体]?[：:]\s*([^\n]+)',
                r'vulnerable[": ]+([^",}\n]+)',
                r'是否[：:]\s*([^\n]+)'
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
                if "概念" in response_text or "利率" in response_text or "术语" in response_text:
                    reasoning = "涉及金融概念理解相关问题"
                elif "决策" in response_text or "成本" in response_text or "风险" in response_text:
                    reasoning = "涉及金融决策能力相关问题"
                elif "权益" in response_text or "维权" in response_text or "监管" in response_text:
                    reasoning = "涉及金融权益认知相关问题"
                else:
                    reasoning = "基于投诉内容的综合评估"
            
            # 文本解析中不再尝试提取维度
            strong_dimensions = []
            weak_dimensions = []
            
            if vulnerability_status:
                category_id = self.vulnerability_mapping.get(vulnerability_status, 2)
                return {
                    "category_id": category_id,
                    "category_name": vulnerability_status,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "strong_dimensions": strong_dimensions,
                    "weak_dimensions": weak_dimensions
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
                    output_file = f"{base_name}_金融素养分类_前{sample_size}条.xlsx"
                else:
                    output_file = f"{base_name}_金融素养分类_全部.xlsx"
            
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
                # 新增金融素养分类相关列
                df['category_id'] = -2  # -2 表示未处理
                df['category_name'] = ''
                df['confidence'] = ''
                df['reasoning'] = ''
                df['strong_dimensions'] = ''
                df['weak_dimensions'] = ''
                # 在初始化新处理的部分添加：
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
                
                logging.info("金融素养分类完成！")
                
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
            1: "是(弱势群体)",
            0: "否(非弱势群体)", 
            2: "不确定",
            3: "非金融相关",
            -1: "Error",
            -2: "未处理"
        }
        
        stats = df['category_id'].value_counts().sort_index()
        print("\n" + "="*50)
        print("金融素养分类统计结果")
        print("="*50)
        
        total_records = len(df)
        for category_id, count in stats.items():
            category_name = category_names.get(category_id, f"未知({category_id})")
            percentage = (count / total_records) * 100
            print(f"{category_id}. {category_name}: {count} 条 ({percentage:.1f}%)")
        
        # 计算关键指标
        vulnerable_count = len(df[df['category_id'] == 1])
        non_vulnerable_count = len(df[df['category_id'] == 0])
        uncertain_count = len(df[df['category_id'] == 2])
        non_financial_count = len(df[df['category_id'] == 3])
        error_count = len(df[df['category_id'] == -1])
        unprocessed_count = len(df[df['category_id'] == -2])
        
        financial_related_count = vulnerable_count + non_vulnerable_count + uncertain_count
        
        print("\n" + "="*50)
        print("关键指标汇总")
        print("="*50)
        print(f"总记录数: {total_records}")
        print(f"金融相关投诉: {financial_related_count} 条 ({(financial_related_count/total_records)*100:.1f}%)")
        print(f"├─ 金融素养弱势群体: {vulnerable_count} 条 ({(vulnerable_count/total_records)*100:.1f}%)")
        print(f"├─ 非弱势群体: {non_vulnerable_count} 条 ({(non_vulnerable_count/total_records)*100:.1f}%)")
        print(f"└─ 不确定: {uncertain_count} 条 ({(uncertain_count/total_records)*100:.1f}%)")
        print(f"非金融相关投诉: {non_financial_count} 条 ({(non_financial_count/total_records)*100:.1f}%)")
        
        if financial_related_count > 0:
            vulnerable_rate = (vulnerable_count / financial_related_count) * 100
            print(f"\n金融相关投诉中弱势群体比例: {vulnerable_rate:.1f}%")
        
        # 输出维度分布统计
        if 'weak_dimensions' in df.columns:
            weak_dimension_stats = {}
            for dimensions in df['weak_dimensions']:
                if dimensions and isinstance(dimensions, str):
                    for dim in dimensions.split(';'):
                        if dim:
                            weak_dimension_stats[dim] = weak_dimension_stats.get(dim, 0) + 1
            
            if weak_dimension_stats:
                print(f"\n主要薄弱维度分布:")
                for dim, count in sorted(weak_dimension_stats.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / vulnerable_count) * 100 if vulnerable_count > 0 else 0
                    print(f"  {dim}: {count} 次提及 ({percentage:.1f}%的弱势群体案例)")

def main():
    """主函数 - 直接运行即可"""
    
    # ========== 配置区域 ==========
    
    # 1. 设置您的API密钥
    API_KEY = "sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol"
    # API_KEY = "sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc"
    
    
    # 2. 设置输入文件路径
    # input_file = "/Users/chenyaxin/Desktop/审稿修改/分类数据/投诉数据_一级样本_10000条_from0_size1000.xlsx"
    input_file = "/Users/chenyaxin/Desktop/审稿修改/分类数据/样本_1000条_20251124_130104.xlsx"
    
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
        print("金融素养分类任务完成！")
        print("="*60)
        
        # 显示结果文件路径
        output_file = input_file.replace('.xlsx', f'_三维度金融素养分类_前{sample_size}条.xlsx') if sample_size else input_file.replace('.xlsx', '_金融素养分类_全部.xlsx')
        print(f"结果已保存至: {output_file}")
        
    except FileNotFoundError:
        print(f"错误：找不到输入文件 '{input_file}'")
        print("请检查文件路径是否正确")
    except Exception as e:
        print(f"分类过程中出错: {e}")
        print("请检查API密钥和网络连接")

if __name__ == "__main__":
    main()