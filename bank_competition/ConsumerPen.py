import pandas as pd
from openai import OpenAI
import time
import logging
import os

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
    
    def classify_single_fact(self, penalty_fact):
        """对单个违规事实进行分类"""
        try:
            prompt = self.prompt_template.format(penalty_fact=penalty_fact)
            
            response = self.client.chat.completions.create(
                model="Qwen/Qwen3-32B",
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_response(result)
            
        except Exception as e:
            logging.error(f"分类失败: {e}")
            return {"classification": "Error", "reason": f"API调用失败: {str(e)}"}
    
    def _parse_response(self, response_text):
        """解析API返回的JSON结果"""
        try:
            import json
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
    
    def batch_classify(self, input_file, output_file, max_records=100, save_batch_size=20, delay=1):
        """批量分类主函数 - 支持数量控制和分批写入"""
        try:
            # 读取数据
            logging.info(f"正在读取数据文件: {input_file}")
            df = pd.read_excel(input_file)
            
            # 检查必要的列
            if '主要违法违规事实' not in df.columns:
                raise ValueError("数据文件中必须包含'主要违法违规事实'列")
            
            # 添加结果列
            df['classification'] = ''
            df['classification_reason'] = ''
            
            # 限制处理数量
            total_to_process = min(max_records, len(df))
            logging.info(f"计划处理 {total_to_process} 条记录（最多{max_records}条）")
            
            processed_count = 0
            batch_count = 0
            
            for i, (idx, row) in enumerate(df.iterrows()):
                if i >= max_records:
                    logging.info(f"已达到最大处理数量 {max_records}，停止处理")
                    break
                
                penalty_fact = str(row['主要违法违规事实']).strip()
                
                if not penalty_fact or penalty_fact == 'nan':
                    df.at[idx, 'classification'] = 'Skip'
                    df.at[idx, 'classification_reason'] = '违规事实为空'
                    continue
                
                # 调用API分类
                result = self.classify_single_fact(penalty_fact)
                df.at[idx, 'classification'] = result['classification']
                df.at[idx, 'classification_reason'] = result['reason']
                
                processed_count += 1
                
                # 进度提示
                if processed_count % 10 == 0:
                    logging.info(f"已处理 {processed_count}/{total_to_process} 条记录")
                
                # 分批保存
                if processed_count % save_batch_size == 0:
                    batch_count += 1
                    temp_output = output_file.replace('.xlsx', f'_batch_{batch_count}.xlsx')
                    df_head = df.head(i+1)  # 保存已处理的部分
                    df_head.to_excel(temp_output, index=False)
                    logging.info(f"第{batch_count}批数据已保存至: {temp_output}")
                
                # 延迟以避免API限制
                time.sleep(delay)
            
            # 最终保存完整结果
            final_df = df.head(processed_count) if processed_count < len(df) else df
            final_df.to_excel(output_file, index=False)
            logging.info(f"最终结果已保存至: {output_file}")
            
            # 输出统计信息
            self._print_statistics(final_df)
            
            logging.info("处理完成！")
            return final_df
            
        except Exception as e:
            logging.error(f"批量处理失败: {e}")
            raise
    
    def _print_statistics(self, df):
        """打印分类统计信息"""
        stats = df['classification'].value_counts()
        print("\n=== 分类统计 ===")
        for cls, count in stats.items():
            percentage = (count / len(df)) * 100
            print(f"{cls}类: {count} 条 ({percentage:.1f}%)")
        
        # 显示前几条结果用于检查
        print("\n=== 前5条分类结果样例 ===")
        sample_df = df[['主要违法违规事实', 'classification', 'classification_reason']].head()
        for _, row in sample_df.iterrows():
            print(f"违规事实: {row['主要违法违规事实'][:50]}...")
            print(f"分类: {row['classification']}, 理由: {row['classification_reason']}")
            print("-" * 50)

# 使用示例 - 测试100条
if __name__ == "__main__":
    # 替换为您的API密钥
    API_KEY = "sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol"
    
    # 创建分类器实例
    classifier = PenaltyClassifier(API_KEY)
    
    # 设置文件路径
    input_file = "/Users/chenyaxin/Desktop/2019年完整行政处罚记录.xlsx"
    output_file = "/Users/chenyaxin/Desktop/行政处罚数据_分类结果.xlsx"
    
    # 执行批量分类 - 只处理100条，每20条保存一次
    try:
        result_df = classifier.batch_classify(
            input_file=input_file,
            output_file=output_file,
            max_records=3000,        # 控制运行数量：100条
            save_batch_size=20,     # 分批写入：每20条保存一次
            delay=1                 # 请求间隔
        )
        
        print(f"\n测试完成！共处理了 {len(result_df)} 条记录")
        print(f"最终结果保存至: {output_file}")
        print("请检查前5条样例，根据结果调整prompt")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")