import pandas as pd
from openai import OpenAI
import time
import logging
import os
import json
import shutil
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PenaltyClassifier:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        self.prompt_template = """请严格遵循以下分类标准，将下列行政处罚的"主要违规事实"归入且仅归入一个类别：

【A类：核心相关】
- **定义**：违规行为直接侵害**个人消费者（自然人）** 的合法权益，或者**通过破坏销售、服务环节的合规性，间接但必然导致消费者权益受损**。
- **关键判断原则**：如果违规行为会让个人消费者面临**销售误导、信息不透明、服务缺失、资金安全风险**等直接危害，就属于A类。
- **关键词/情形举例**：
  - **销售渠道违规**：委托无资格机构销售、与无资质第三方合作、通过非法渠道开展业务。
  - **信息披露**：虚假宣传、夸大收益、隐瞒风险、模糊条件、强制搭售。
  - **营销宣传**：误导销售、欺诈诱导、不当营销。
  - **个人信息保护**：未经同意收集/使用/泄露个人信息。
  - **公平交易**：捆绑销售、不公平定价、合同含有不公平格式条款。
  - **自主选择**：强制搭售、强制接受服务。
  - **财产安全**：不当催收、违规扣费、资金划转不合规。
  - **信息安全**：因内控漏洞导致消费者信息泄露。

【B类：弱相关或无关】
- **定义**：违规行为主要涉及机构**内部治理、审慎经营规则、或对公/同业业务**，与个人消费者权益无直接关联。
- **关键判断原则**：如果违规行为主要影响的是**机构间的业务往来、内部管理流程、监管合规要求**，而不直接涉及对个人消费者的销售和服务环节，就属于B类。
- **关键词/情形举例**：
  - **审慎经营**：贷款三查不尽职、信贷资金违规流入房地产市场/股市、资本充足率不足、拨备覆盖率不足。
  - **内部治理**：公司治理不健全、股东股权管理混乱、关联交易不合规、内部审计缺失。
  - **数据与报告**：监管数据报送错误/瞒报/漏报、统计业务数据不真实。
  - **同业与金融市场业务**：同业业务违规、票据业务违规、债券投资违规。
  - **反洗钱**：未履行客户身份识别义务、未提交大额和可疑交易报告。
  - **其他**：未经批准设立分支机构、高管任职未经核准。

**重要区分指引**：
1. 涉及**销售渠道、营销方式、客户服务**的违规，即使表面是管理问题，也归为A类
2. 涉及**资金运用、内部流程、数据报送**的违规，如不直接涉及消费者，归为B类

输出要求：
1. **输出格式**：严格JSON格式，包含：
   - "classification": 分类结果，只允许填写 "A" 或 "B"
   - "reason": 简要说明归类理由，不超过20字
2. 请勿输出任何其他解释性文字。

待分类的"主要违法违规事实"：
"{penalty_fact}"
"""
    
    def classify_single_fact(self, penalty_fact, max_retries=3):
        """对单个违规事实进行分类，支持重试"""
        for attempt in range(max_retries):
            try:
                prompt = self.prompt_template.format(penalty_fact=penalty_fact)
                
                response = self.client.chat.completions.create(
                    model="Qwen/Qwen2.5-72B-Instruct",
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                
                result = response.choices[0].message.content.strip()
                parsed_result = self._parse_response(result)
                
                # 如果解析成功且不是错误，直接返回
                if parsed_result["classification"] not in ["Error", "Skip"]:
                    return parsed_result
                else:
                    logging.warning(f"第{attempt+1}次尝试返回错误，准备重试: {parsed_result['reason']}")
                    
            except Exception as e:
                logging.error(f"第{attempt+1}次分类失败: {e}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                time.sleep(2)  # 重试前等待2秒
        
        # 所有重试都失败
        return {"classification": "Error", "reason": f"经过{max_retries}次重试后仍失败"}
    
    def _parse_response(self, response_text):
        """解析API返回的JSON结果"""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                if "classification" in result and "reason" in result:
                    if result["classification"] in ["A", "B"]:
                        return result
                    else:
                        return {"classification": "Error", "reason": "分类结果不是A或B"}
                else:
                    return {"classification": "Error", "reason": "返回格式缺少必要字段"}
            else:
                return {"classification": "Error", "reason": "未找到有效的JSON响应"}
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {e}, 原始响应: {response_text}")
            return {"classification": "Error", "reason": f"JSON解析失败: {str(e)}"}
    
    def retry_error_classifications(self, result_file, output_file=None, 
                                   max_retries=3, save_batch_size=20, delay=1,
                                   checkpoint_file=None):
        """
        专门重新处理分类结果为Error的记录，支持断点续传
        
        参数:
        - result_file: 已有的结果文件路径（包含原始数据和已有的分类结果）
        - output_file: 最终输出文件路径，如果为None则覆盖原文件
        - max_retries: 最大重试次数
        - save_batch_size: 分批保存大小
        - delay: 请求间隔时间
        - checkpoint_file: 检查点文件路径，用于断点续传
        """
        try:
            # 设置输出文件
            if output_file is None:
                output_file = result_file
            
            # 设置检查点文件
            if checkpoint_file is None:
                checkpoint_file = output_file.replace('.xlsx', '_checkpoint.json')
            
            # 读取已有结果
            logging.info(f"正在读取结果文件: {result_file}")
            df = pd.read_excel(result_file)
            
            # 检查必要的列
            required_columns = ['主要违法违规事实', 'classification', 'classification_reason']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"结果文件中必须包含'{col}'列")
            
            # 检查是否有检查点文件，如果有则从中断处继续
            processed_indices = set()
            if os.path.exists(checkpoint_file):
                logging.info(f"发现检查点文件: {checkpoint_file}，将从断点继续")
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    processed_indices = set(checkpoint_data.get('processed_indices', []))
                
                # 更新DataFrame中的已处理记录
                for idx in processed_indices:
                    if idx in df.index:
                        # 从检查点文件中恢复已处理的结果
                        if 'results' in checkpoint_data and str(idx) in checkpoint_data['results']:
                            result = checkpoint_data['results'][str(idx)]
                            df.at[idx, 'classification'] = result['classification']
                            df.at[idx, 'classification_reason'] = result['reason']
            
            # 找出所有未处理的Error记录
            error_mask = (df['classification'] == 'Error') & (~df.index.isin(processed_indices))
            error_indices = df[error_mask].index.tolist()
            
            if not error_indices:
                logging.info("没有找到需要重试的Error记录")
                # 清理检查点文件
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
                return df
            
            logging.info(f"找到 {len(error_indices)} 条未处理的Error记录需要重新处理")
            
            # 创建结果文件的备份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = result_file.replace('.xlsx', f'_backup_{timestamp}.xlsx')
            df.to_excel(backup_file, index=False)
            logging.info(f"已创建备份文件: {backup_file}")
            
            # 分批处理Error记录
            total_errors = len(error_indices)
            processed_count = 0
            batch_count = 0
            
            try:
                for i, idx in enumerate(error_indices):
                    penalty_fact = str(df.at[idx, '主要违法违规事实']).strip()
                    
                    if not penalty_fact or penalty_fact == 'nan':
                        df.at[idx, 'classification'] = 'Skip'
                        df.at[idx, 'classification_reason'] = '违规事实为空'
                        processed_indices.add(idx)
                        processed_count += 1
                        continue
                    
                    # 重新分类
                    logging.info(f"重新处理第 {i+1}/{total_errors} 条Error记录")
                    result = self.classify_single_fact(penalty_fact, max_retries=max_retries)
                    
                    # 更新结果
                    df.at[idx, 'classification'] = result['classification']
                    df.at[idx, 'classification_reason'] = result['reason']
                    
                    # 更新已处理索引
                    processed_indices.add(idx)
                    processed_count += 1
                    
                    # 进度提示
                    if processed_count % 10 == 0:
                        success_count = len(df[df['classification'].isin(['A', 'B'])])
                        remaining_errors = len(df[df['classification'] == 'Error'])
                        logging.info(f"已重新处理 {processed_count}/{total_errors} 条Error记录，成功分类: {success_count} 条，剩余Error: {remaining_errors} 条")
                    
                    # 分批保存和检查点
                    if processed_count % save_batch_size == 0:
                        batch_count += 1
                        
                        # 保存检查点
                        self._save_checkpoint(checkpoint_file, processed_indices, df, error_indices)
                        
                        # 保存当前进度到临时文件
                        temp_output = output_file.replace('.xlsx', f'_inprogress_{batch_count}.xlsx')
                        df.to_excel(temp_output, index=False)
                        logging.info(f"第{batch_count}批数据已保存至: {temp_output}")
                    
                    # 延迟以避免API限制
                    time.sleep(delay)
                
                # 处理完成，保存最终结果
                df.to_excel(output_file, index=False)
                logging.info(f"最终结果已保存至: {output_file}")
                
                # 清理检查点文件和临时文件
                if os.path.exists(checkpoint_file):
                    os.remove(checkpoint_file)
                
                # 清理临时文件
                for file in os.listdir(os.path.dirname(output_file)):
                    if file.startswith(os.path.basename(output_file).replace('.xlsx', '_inprogress_')):
                        os.remove(os.path.join(os.path.dirname(output_file), file))
                
                # 输出统计信息
                self._print_retry_statistics(df, total_errors)
                
                logging.info("Error记录重试完成！")
                
            except KeyboardInterrupt:
                logging.info("程序被用户中断，保存当前进度...")
                # 保存检查点
                self._save_checkpoint(checkpoint_file, processed_indices, df, error_indices)
                # 保存当前进度
                temp_output = output_file.replace('.xlsx', '_interrupted.xlsx')
                df.to_excel(temp_output, index=False)
                logging.info(f"中断时的进度已保存至: {temp_output}")
                logging.info(f"下次运行将从断点继续，已处理 {processed_count}/{total_errors} 条记录")
                raise
                
            except Exception as e:
                logging.error(f"处理过程中出错: {e}")
                # 保存检查点
                self._save_checkpoint(checkpoint_file, processed_indices, df, error_indices)
                # 保存当前进度
                temp_output = output_file.replace('.xlsx', '_error.xlsx')
                df.to_excel(temp_output, index=False)
                logging.info(f"出错时的进度已保存至: {temp_output}")
                raise
            
            return df
            
        except Exception as e:
            logging.error(f"重试Error记录失败: {e}")
            raise
    
    def _save_checkpoint(self, checkpoint_file, processed_indices, df, error_indices):
        """保存检查点文件"""
        try:
            # 收集已处理记录的结果
            results = {}
            for idx in processed_indices:
                if idx in df.index:
                    results[str(idx)] = {
                        'classification': df.at[idx, 'classification'],
                        'reason': df.at[idx, 'classification_reason']
                    }
            
            checkpoint_data = {
                'timestamp': datetime.now().isoformat(),
                'processed_indices': list(processed_indices),
                'total_error_count': len(error_indices),
                'results': results
            }
            
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            
            logging.debug(f"检查点已保存: {checkpoint_file}")
            
        except Exception as e:
            logging.error(f"保存检查点失败: {e}")
    
    def _print_retry_statistics(self, df, total_errors_retried):
        """打印重试后的统计信息"""
        stats = df['classification'].value_counts()
        print("\n=== 重试后分类统计 ===")
        for cls, count in stats.items():
            percentage = (count / len(df)) * 100
            print(f"{cls}类: {count} 条 ({percentage:.1f}%)")
        
        success_after_retry = len(df[df['classification'].isin(['A', 'B'])])
        still_errors = len(df[df['classification'] == 'Error'])
        
        print(f"\n=== 重试效果统计 ===")
        print(f"本次重试Error记录数量: {total_errors_retried}")
        print(f"重试后成功分类数量: {success_after_retry}")
        print(f"重试后仍为Error数量: {still_errors}")
        if total_errors_retried > 0:
            success_rate = ((total_errors_retried - still_errors) / total_errors_retried) * 100
            print(f"重试成功率: {success_rate:.1f}%")
        
        # 显示前几条重试结果用于检查
        print("\n=== 前5条重试结果样例 ===")
        # 找出最近被重试的记录（即原来是Error现在不是的记录）
        retried_samples = df.head(min(5, len(df)))
        for _, row in retried_samples.iterrows():
            fact_preview = row['主要违法违规事实'][:50] + "..." if len(row['主要违法违规事实']) > 50 else row['主要违法违规事实']
            print(f"违规事实: {fact_preview}")
            print(f"分类: {row['classification']}, 理由: {row['classification_reason']}")
            print("-" * 50)

# 使用示例 - 专门重试Error记录，支持断点续传
if __name__ == "__main__":
    # 替换为您的API密钥
    API_KEY = "sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol"
    
    # 创建分类器实例
    classifier = PenaltyClassifier(API_KEY)
    
    # 设置文件路径
    result_file = "/Users/chenyaxin/Desktop/信息规范/data/行政处罚分类结果_消费者.xlsx"  # 已有结果文件（包含原始数据和部分分类结果）
    output_file = "/Users/chenyaxin/Desktop/行政处罚数据_分类结果_重试后.xlsx"  # 最终输出文件
    checkpoint_file = "/Users/chenyaxin/Desktop/checkpoint.json"  # 检查点文件
    
    # 专门重试Error记录
    try:
        final_df = classifier.retry_error_classifications(
            result_file=result_file,
            output_file=output_file,
            max_retries=3,           # 每条Error记录最多重试3次
            save_batch_size=20,      # 每20条保存一次
            delay=1,                 # 请求间隔1秒
            checkpoint_file=checkpoint_file  # 检查点文件
        )
        
        print(f"\nError记录重试完成！")
        print(f"最终结果保存至: {output_file}")
        
        # 显示最终统计
        error_count = len(final_df[final_df['classification'] == 'Error'])
        total_count = len(final_df)
        success_count = len(final_df[final_df['classification'].isin(['A', 'B'])])
        print(f"总记录数: {total_count}, 成功分类: {success_count}, 剩余Error数量: {error_count}")
        
    except KeyboardInterrupt:
        print("程序被用户中断，下次运行将从断点继续")
    except Exception as e:
        print(f"重试过程中出错: {e}")