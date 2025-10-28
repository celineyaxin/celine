import pandas as pd
import random
import json
from openai import OpenAI
import time
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PenaltyDataSampler:
    def __init__(self, excel_path):
        self.df = pd.read_excel(excel_path)
        self.sampled_data = None
    
    def filter_2019_data(self):
        """筛选2019年的数据"""
        if '处罚年' in self.df.columns:
            self.df_2019 = self.df[self.df['处罚年'] == 2019]
        elif '作出处罚决定的日期' in self.df.columns:
            self.df_2019 = self.df[self.df['作出处罚决定的日期'].str.contains('2019', na=False)]
        else:
            # 如果没有明确年份列，可能需要手动处理
            raise ValueError("请确保Excel中包含年份信息")
        
        logger.info(f"2019年行政处罚记录总数: {len(self.df_2019)}")
        return self.df_2019
    
    def stratified_sampling(self, n=500, company_col='所属公司'):
        """分层抽样：按公司均匀抽取"""
        # 按公司分组
        company_groups = self.df_2019.groupby(company_col)
        
        # 计算每个公司应该抽取的数量
        companies = list(company_groups.groups.keys())
        n_companies = len(companies)
        
        if n_companies == 0:
            raise ValueError("没有找到公司分组信息")
        
        # 基础抽样：每个公司至少抽1条
        base_samples_per_company = 1
        remaining_samples = n - (n_companies * base_samples_per_company)
        
        if remaining_samples < 0:
            # 如果公司数量超过500，随机选择500家公司
            selected_companies = random.sample(companies, n)
            sampled_data = []
            for company in selected_companies:
                company_data = company_groups.get_group(company)
                sampled_data.append(company_data.sample(n=1))
            self.sampled_data = pd.concat(sampled_data, ignore_index=True)
        else:
            # 分层抽样
            sampled_data = []
            
            # 第一阶段：每个公司至少抽1条
            for company in companies:
                company_data = company_groups.get_group(company)
                if len(company_data) >= base_samples_per_company:
                    sampled = company_data.sample(n=base_samples_per_company)
                    sampled_data.append(sampled)
            
            # 第二阶段：按比例分配剩余样本
            company_sizes = {company: len(group) for company, group in company_groups}
            total_records = sum(company_sizes.values())
            
            for company in companies:
                company_data = company_groups.get_group(company)
                already_sampled = base_samples_per_company
                additional_samples = int((company_sizes[company] / total_records) * remaining_samples)
                
                if additional_samples > 0 and (len(company_data) - already_sampled) >= additional_samples:
                    additional_sampled = company_data.drop(sampled_data[-1].index).sample(n=additional_samples)
                    sampled_data.append(additional_sampled)
            
            self.sampled_data = pd.concat(sampled_data, ignore_index=True)
            
            # 如果样本量不足，补充随机抽样
            if len(self.sampled_data) < n:
                remaining = n - len(self.sampled_data)
                remaining_data = self.df_2019.drop(self.sampled_data.index)
                additional = remaining_data.sample(n=min(remaining, len(remaining_data)))
                self.sampled_data = pd.concat([self.sampled_data, additional], ignore_index=True)
        
        logger.info(f"分层抽样完成，共抽取 {len(self.sampled_data)} 条记录")
        logger.info(f"涉及公司数量: {self.sampled_data[company_col].nunique()}")
        return self.sampled_data
    
    def save_sampled_data(self, output_path):
        """保存抽样结果"""
        if self.sampled_data is not None:
            self.sampled_data.to_excel(output_path, index=False)
            logger.info(f"抽样数据已保存至: {output_path}")
        else:
            logger.warning("没有抽样数据可保存")

class ViolationClassifier:
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = "Qwen/Qwen3-32B"
        
        # 针对金融营销宣传违规的判断提示词
        self.system_prompt = """你是一位金融监管合规分析专家。请严格根据《关于进一步规范金融营销宣传行为的通知》及相关监管要求，判断给定的行政处罚案例中的"主要违法违规事实"是否属于"金融营销宣传违规"。

请仅根据案例中描述的"主要违法违规事实"进行分析。

**金融营销宣传违规的主要特征包括：**
1. 虚假宣传、误导性宣传
2. 未充分揭示风险、承诺收益
3. 不当营销、欺诈营销
4. 互联网营销违规
5. 销售误导、欺骗投保人
6. 宣传材料不规范
7. 利用政府公信力进行营销
8. 其他违反金融营销宣传规定的行为

**输出要求：**
请以JSON格式输出判断结果和理由：
{
  "is_marketing_violation": true/false,
  "confidence": "高/中/低",
  "reasoning": "简要说明判断理由，指出其具体违反了哪条金融营销宣传规定。如果判断为违规，请说明违规类型。"
}

请严格基于事实进行判断，不要推测。"""
    
    def classify_violation(self, violation_text: str) -> dict:
        """对单条违规事实进行分类"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"请分析以下主要违法违规事实：{violation_text}"}
                ],
                temperature=0.1,
                max_tokens=300,
                stream=False
            )
            
            result_text = response.choices[0].message.content.strip()
            
            try:
                result = json.loads(result_text)
                result["api_success"] = True
                return result
            except json.JSONDecodeError:
                # 尝试提取JSON
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result_text[start:end]
                    result = json.loads(json_str)
                    result["api_success"] = True
                    return result
                else:
                    return {
                        "is_marketing_violation": False,
                        "confidence": "低",
                        "reasoning": "API返回格式错误",
                        "api_success": False
                    }
                    
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            return {
                "is_marketing_violation": False,
                "confidence": "低",
                "reasoning": f"API调用失败: {str(e)}",
                "api_success": False
            }
    
    def batch_classify(self, sampled_df: pd.DataFrame, violation_col: str = "主要违法违规事实", 
                      delay: float = 0.5) -> pd.DataFrame:
        """批量分类违规事实"""
        results = []
        total = len(sampled_df)
        
        for idx, row in sampled_df.iterrows():
            violation_text = row[violation_col]
            logger.info(f"分类进度: {idx+1}/{total} - 违规事实: {violation_text[:50]}...")
            
            classification_result = self.classify_violation(violation_text)
            
            # 合并结果
            result_row = row.to_dict()
            result_row.update(classification_result)
            results.append(result_row)
            
            # 控制请求频率
            if idx < total - 1:
                time.sleep(delay)
        
        return pd.DataFrame(results)
    
def main():
    # 配置
    API_KEY = "sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol"
    EXCEL_PATH = "/Users/chenyaxin/Downloads/提取所属公司.xlsx"
    
    # 第一步：分层抽样
    logger.info("开始分层抽样...")
    sampler = PenaltyDataSampler(EXCEL_PATH)
    df_2019 = sampler.filter_2019_data()
    sampled_df = sampler.stratified_sampling(n=500, company_col='所属公司')
    sampler.save_sampled_data("/Users/chenyaxin/Desktop/sampled_penalties.xlsx")
    
    # 第二步：违规分类
    logger.info("开始违规分类...")
    classifier = ViolationClassifier(api_key=API_KEY)
    classified_df = classifier.batch_classify(sampled_df, violation_col="主要违法违规事实")
    
    # 保存最终结果
    output_path = "/Users/chenyaxin/Desktop/classified_penalties.xlsx"
    classified_df.to_excel(output_path, index=False)
    logger.info(f"分类完成，结果已保存至: {output_path}")
    
    # 统计结果
    marketing_violations = classified_df[classified_df['is_marketing_violation'] == True]
    high_confidence = marketing_violations[marketing_violations['confidence'] == '高']
    
    print(f"\n=== 分析结果 ===")
    print(f"总样本量: {len(classified_df)}")
    print(f"识别为营销宣传违规: {len(marketing_violations)} ({len(marketing_violations)/len(classified_df)*100:.1f}%)")
    print(f"高置信度违规: {len(high_confidence)}")
    print(f"API调用成功率: {len(classified_df[classified_df['api_success'] == True])/len(classified_df)*100:.1f}%")
    
    # 显示部分高置信度违规案例
    if len(high_confidence) > 0:
        print(f"\n高置信度营销宣传违规案例示例:")
        for _, row in high_confidence.head(3).iterrows():
            print(f"- {row['主要违法违规事实'][:100]}...")
            print(f"  理由: {row['reasoning']}")

if __name__ == "__main__":
    main()