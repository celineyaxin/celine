import pandas as pd
from openai import OpenAI
import time
import logging
import os
from datetime import datetime
import re

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FinancialVulnerabilityAugmentor:
    def __init__(self, api_key):
        # 使用与您能跑通代码完全相同的配置
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
            # 不设置timeout，使用默认值
        )
        
        # 更新为金融素养弱势群体变体生成的prompt
        self.prompt_template = """作为金融行为分析专家，请基于以下金融素养弱势群体的投诉文本，生成3个变体：

**金融素养弱势群体的核心特征**：
1. **金融概念理解不足**：不理解基本金融术语（如年化利率、手续费、违约金），混淆利率类型，或无法理解金融产品的基本机制
2. **金融决策能力不足**：缺乏理性借贷决策过程，如未比较产品、未评估还款能力、冲动借款、过度负债
3. **金融权益认知不足**：不了解消费者基本权利，不知道正规维权渠道

### 生成要求
基于您对金融素养弱势群体的深刻理解，生成3个变体，每个必须：
- 保持相同的弱势群体特征（从原始文本中识别出的特征）
- 改变具体表述但保持核心认知缺陷机制
- 确保变体自然真实，符合投诉场景
- **重要：不要在变体文本中添加任何类型标签或方括号，只输出纯文本的投诉内容**

### 特别注意
- 变体必须体现明确的金融素养不足证据，不能仅是情绪表达
- 保持投诉的真实性和可信度
- 避免过度夸张或不合理的表述

**金融素养弱势群体典型表现示例**：
- "我不懂什么是年利率，他们说什么就是什么"
- "借钱时没想那么多，就是急用钱"
- "不知道可以投诉，也不了解合法利率范围"
- "分不清日利率和年利率，以为很划算就借了"
- "逾期了也不知道征信是什么，就让他们随便处理"

投诉内容：
"{complaint_text}"

请严格按照以下格式输出，不要添加任何其他内容：
变体1：[生成的文本内容]
变体2：[生成的文本内容]
变体3：[生成的文本内容]"""
    
    def generate_variants(self, complaint_text, max_retries=3):
        """为单个投诉文本生成3个变体"""
        for attempt in range(max_retries):
            try:
                if not complaint_text or len(complaint_text.strip()) < 5:
                    return "内容过短", "内容过短", "内容过短"
                
                prompt = self.prompt_template.format(complaint_text=complaint_text)
                
                # 使用与您能跑通代码相同的参数
                response = self.client.chat.completions.create(
                    model="Qwen/QwQ-32B",   
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.7,
                    max_tokens=1000
                    # 不设置timeout，使用默认值
                )
                
                result_text = response.choices[0].message.content.strip()
                logging.info(f"生成响应: {result_text}")
                
                # 解析变体
                return self._parse_variants(result_text)
                
            except Exception as e:
                logging.error(f"第{attempt+1}次生成失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return "生成失败", "生成失败", "生成失败"
    
    def _parse_variants(self, response_text):
        """解析生成的变体文本"""
        variants = ["", "", ""]
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        
        variant_count = 0
        for line in lines:
            if variant_count >= 3:
                break
                
            # 匹配各种格式的变体标记
            if re.match(r'^(变体[123]|[123])[:：]\s*', line):
                # 提取冒号/中文冒号后的内容
                content = re.sub(r'^(变体[123]|[123])[:：]\s*', '', line)
                if content and len(content) > 5:  # 确保有实际内容
                    variants[variant_count] = content
                    variant_count += 1
        
        # 如果没找到足够变体，尝试其他解析方式
        if variant_count < 3:
            for i, line in enumerate(lines):
                if i < 3 and line and len(line) > 10 and not line.startswith('变体'):
                    variants[i] = line
                    variant_count += 1
        
        return variants[0], variants[1], variants[2]
    
    def augment_complaints(self, input_file, output_file=None, 
                          text_column='complaint_content', max_rows=None,
                          max_retries=3, save_batch_size=10, delay=2):
        """
        数据增强主函数 - 结构与您能跑通的代码保持一致
        """
        try:
            # 设置输出文件
            if output_file is None:
                base_name = os.path.splitext(input_file)[0]
                if max_rows:
                    output_file = f"{base_name}_金融素养弱势群体变体_前{max_rows}条.xlsx"
                else:
                    output_file = f"{base_name}_金融素养弱势群体变体_全部.xlsx"
            
            # 读取原始数据
            logging.info(f"正在读取数据文件: {input_file}")
            df = pd.read_excel(input_file)
            
            # 应用行数限制
            total_records = len(df)
            if max_rows is not None and max_rows < total_records:
                df = df.head(max_rows)
                total_records = max_rows
                logging.info(f"将处理前 {max_rows} 条记录")
            else:
                logging.info(f"将处理全部 {total_records} 条记录")
            
            # 检查必要的列
            if text_column not in df.columns:
                # 尝试自动找到合适的列
                content_columns = [col for col in df.columns if any(keyword in col for keyword in ['投诉', '内容', 'content', 'text', 'complaint'])]
                if content_columns:
                    text_column = content_columns[0]
                    logging.info(f"自动选择列: {text_column}")
                else:
                    raise ValueError(f"未找到合适的文本列，可用列: {df.columns.tolist()}")
            
            # 添加新列
            df['variant_1'] = ''
            df['variant_2'] = ''
            df['variant_3'] = ''
            df['generation_status'] = '待处理'
            df['generation_timestamp'] = ''
            
            # 检查是否已经有部分处理过的文件，支持断点续传
            if os.path.exists(output_file):
                try:
                    existing_df = pd.read_excel(output_file)
                    if len(existing_df) == len(df) and 'variant_1' in existing_df.columns:
                        # 复制已处理的结果
                        processed_mask = existing_df['generation_status'].isin(['已完成', '部分失败'])
                        df.loc[processed_mask, 'variant_1'] = existing_df.loc[processed_mask, 'variant_1']
                        df.loc[processed_mask, 'variant_2'] = existing_df.loc[processed_mask, 'variant_2']
                        df.loc[processed_mask, 'variant_3'] = existing_df.loc[processed_mask, 'variant_3']
                        df.loc[processed_mask, 'generation_status'] = existing_df.loc[processed_mask, 'generation_status']
                        df.loc[processed_mask, 'generation_timestamp'] = existing_df.loc[processed_mask, 'generation_timestamp']
                        
                        processed_count = processed_mask.sum()
                        logging.info(f"从现有文件恢复: 已处理 {processed_count}/{total_records} 条记录")
                except Exception as e:
                    logging.warning(f"读取现有文件失败，将重新开始: {e}")
            
            logging.info(f"开始处理 {total_records} 条记录")
            
            # 处理每条记录
            for i in range(total_records):
                # 跳过已处理的记录
                if df.at[i, 'generation_status'] in ['已完成', '部分失败']:
                    continue
                    
                complaint_text = str(df.at[i, text_column]).strip()
                
                # 跳过空文本
                if not complaint_text or complaint_text == 'nan':
                    df.at[i, 'generation_status'] = '跳过（空文本）'
                    df.at[i, 'generation_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    continue
                
                current_progress = i + 1
                logging.info(f"处理第 {current_progress}/{total_records} 条记录")
                logging.info(f"原文: {complaint_text[:100]}...")
                
                # 生成变体
                v1, v2, v3 = self.generate_variants(complaint_text, max_retries=max_retries)
                
                # 更新结果
                df.at[i, 'variant_1'] = v1
                df.at[i, 'variant_2'] = v2
                df.at[i, 'variant_3'] = v3
                df.at[i, 'generation_status'] = '已完成' if v1 != "生成失败" and v2 != "生成失败" and v3 != "生成失败" else '部分失败'
                df.at[i, 'generation_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                logging.info(f"生成结果: {v1[:50]}...")
                
                # 分批保存
                if (current_progress) % save_batch_size == 0:
                    df.to_excel(output_file, index=False)
                    logging.info(f"已保存进度: {current_progress}/{total_records}")
                
                # 延迟
                time.sleep(delay)
            
            # 最终保存
            df.to_excel(output_file, index=False)
            logging.info(f"处理完成! 结果保存至: {output_file}")
            
            # 统计信息
            self._print_statistics(df)
            
            return df
            
        except Exception as e:
            logging.error(f"处理失败: {e}")
            # 出错时也尝试保存当前进度
            if 'df' in locals():
                df.to_excel(output_file, index=False)
                logging.info(f"出错时的进度已保存至: {output_file}")
            raise
    
    def _print_statistics(self, df):
        """打印处理统计信息"""
        status_counts = df['generation_status'].value_counts()
        
        print("\n" + "="*50)
        print("金融素养弱势群体变体生成统计")
        print("="*50)
        
        total_records = len(df)
        for status, count in status_counts.items():
            percentage = (count / total_records) * 100
            print(f"{status}: {count} 条 ({percentage:.1f}%)")
        
        # 计算成功生成的数量
        success_count = len(df[df['generation_status'] == '已完成'])
        print(f"\n成功生成三个变体: {success_count}/{total_records} ({success_count/total_records*100:.1f}%)")
        print("="*50)

def main():
    """主函数 - 使用与您能跑通代码相同的结构"""
    
    # ========== 配置区域 ==========
    API_KEY = "sk-dfxeyyujyasffouikqtgywrraabhoxirlyojqjbowynvnlfc"  # 您的API密钥
    
    # 输入文件路径 - 请修改为您的实际文件路径
    input_file = "/Users/chenyaxin/Desktop/审稿修改/分类数据/用于生成变体的素材.xlsx"
    
    # 处理参数
    max_rows = None  # 测试时设为5，正式运行设为None处理全部
    text_column = "投诉内容"  # 修改为您的文本列名
    
    # ========== 执行区域 ==========
    
    try:
        augmentor = FinancialVulnerabilityAugmentor(API_KEY)
        
        result_df = augmentor.augment_complaints(
            input_file=input_file,
            text_column=text_column,
            max_rows=max_rows,
            max_retries=3,
            save_batch_size=5,
            delay=2
        )
        
        print("金融素养弱势群体变体生成任务完成！")
        
    except Exception as e:
        print(f"执行失败: {e}")

if __name__ == "__main__":
    main()