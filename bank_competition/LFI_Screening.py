from openai import OpenAI
import json
import pandas as pd
import time
import logging
from typing import List, Dict, Any
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialInstitutionClassifier:
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = "Qwen/Qwen3-32B"
        self.checkpoint_file = None
        self.system_prompt = """你是一位精通中国金融监管体系的专家。请根据提供的金融机构简称，严格完成以下任务：

任务要求：
1. **判断是否为持牌机构**：基于简称判断它是否很可能是中国银保监会（现国家金融监督管理总局）监管的持牌银行或保险公司。
2. **提供最有可能的全称**：如果是持牌机构，请给出其最可能的官方全称。
3. **置信度评估**：给出判断的置信度（高/中/低）。

**必须严格按照以下JSON格式输出，不要有任何其他文字：**
{
"original_name": "原始输入名称",
"is_licensed": true/false,
"confidence": "高/中/低", 
"full_name": "最可能的全称，如无法判断则留空",
"reason": "简要的判断理由"
}

【高概率持牌银行/保险特征】
- 名称含"银行"、"农商行"、"村镇银行"、"人寿"、"保险"、"财险"、"寿险"等关键词
- 常见国有大行、股份行、知名险企简称

【明确排除】
- 含"金融科技"、"数科"、"金服"、"POS"、"理财"、"省"等明显非持牌关键词
- 支付工具或优惠平台类名称

判断原则：保守原则，不确定一律判非持牌。"""
    
    def _append_checkpoint(self, result: Dict[str, Any]):
        if self.checkpoint_file is None:
            return
        header = not os.path.isfile(self.checkpoint_file)
        pd.DataFrame([result]).to_csv(
            self.checkpoint_file, mode='a', header=header, index=False, encoding='utf-8-sig'
        )

    def analyze_single_institution(self, name: str) -> Dict[str, Any]:
        try:
            rsp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"请分析这个机构：{name}"}
                ],
                temperature=0.1,
                max_tokens=1000,
                stream=False
            )
            txt = rsp.choices[0].message.content.strip()
            try:
                res = json.loads(txt)
            except json.JSONDecodeError:
                st, ed = txt.find('{'), txt.rfind('}') + 1
                res = json.loads(txt[st:ed]) if st >= 0 and ed > st else {}
            res.update({"original_name": name, "api_success": True})
            return res
        except Exception as e:
            logger.error(f"API 失败: {name} {e}")
            return {
                "original_name": name,
                "is_licensed": False,
                "confidence": "低",
                "full_name": "",
                "reason": f"API 异常: {e}",
                "api_success": False
            }

    def read_excel_data(self, file_path: str, sheet_name=0, column_name="投诉商家") -> List[str]:
        """修复：正确处理 Excel 读取，确保返回 DataFrame"""
        try:
            # 读取 Excel 文件
            if sheet_name is None:
                # 如果不指定工作表，使用第一个工作表
                df = pd.read_excel(file_path, sheet_name=0)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 调试信息
            logger.info(f"读取的 DataFrame 类型: {type(df)}")
            logger.info(f"DataFrame 列名: {list(df.columns) if hasattr(df, 'columns') else 'N/A'}")
            
            # 检查是否是字典（多工作表情况）
            if isinstance(df, dict):
                logger.warning("Excel 包含多个工作表，使用第一个工作表")
                first_sheet = list(df.keys())[0]
                df = df[first_sheet]
            
            # 确保是 DataFrame
            if not isinstance(df, pd.DataFrame):
                raise ValueError(f"读取的数据不是 DataFrame，而是 {type(df)}")
            
            # 检查列是否存在
            if column_name not in df.columns:
                available_columns = list(df.columns)
                raise ValueError(f"列 '{column_name}' 不存在。可用列: {available_columns}")
            
            # 返回机构名称列表
            names = df[column_name].dropna().astype(str).tolist()
            logger.info(f"成功读取 {len(names)} 个机构名称")
            return names
            
        except Exception as e:
            logger.error(f"读取 Excel 文件失败: {str(e)}")
            raise

    def batch_analyze(self, name_list: List[str], delay: float = 0.5,
                      batch_size: int = 20, checkpoint: str = None) -> pd.DataFrame:
        if checkpoint is None:
            checkpoint = os.path.join(os.getcwd(), "fi_checkpoint.csv")
        self.checkpoint_file = checkpoint

        # 初始化结果列表
        results = []
        
        # 如果有断点文件，加载已处理的数据
        if os.path.isfile(checkpoint):
            try:
                done_df = pd.read_csv(checkpoint)
                done_names = set(done_df['original_name'].astype(str).tolist())
                # 将已处理的数据添加到结果中
                results = done_df.to_dict('records')
                logger.info(f"加载已有进度：已完成 {len(done_names)} 条")
            except Exception as e:
                logger.error(f"读取断点文件失败: {e}")
                done_names = set()
        else:
            done_names = set()

        # 找出待处理的名称
        todo = [n for n in name_list if n not in done_names]
        total = len(todo)
        
        logger.info(f"需要处理 {total} 个新机构")

        # 处理新机构
        for idx, name in enumerate(todo, 1):
            logger.info(f"进度 {idx}/{total}  当前：{name}")
            res = self.analyze_single_institution(name)
            results.append(res)
            self._append_checkpoint(res)
            
            # 每处理 batch_size 条生成快照
            if idx % batch_size == 0:
                snap = f"fi_snapshot_{len(results)}.xlsx"
                pd.DataFrame(results).to_excel(snap, index=False)
                logger.info(f">>> 快照已保存：{snap}")
            
            if idx < total:
                time.sleep(delay)
        
        # 确保返回 DataFrame
        return pd.DataFrame(results)

    def process_excel_file(self, input_file: str, output_file: str = None,
                          sheet_name=0, column_name="投诉商家",
                          delay: float = 0.5, batch_size: int = 20) -> pd.DataFrame:
        """修复：确保正确读取 Excel 文件"""
        try:
            # 读取原始数据
            logger.info(f"读取 Excel 文件: {input_file}")
            if sheet_name is None:
                original_df = pd.read_excel(input_file, sheet_name=0)
            else:
                original_df = pd.read_excel(input_file, sheet_name=sheet_name)
            
            # 检查是否是字典（多工作表情况）
            if isinstance(original_df, dict):
                logger.warning("Excel 包含多个工作表，使用第一个工作表")
                first_sheet = list(original_df.keys())[0]
                original_df = original_df[first_sheet]
            
            logger.info(f"原始数据形状: {original_df.shape}")
            logger.info(f"原始数据列名: {list(original_df.columns)}")
            
            # 读取机构名称
            names = self.read_excel_data(input_file, sheet_name, column_name)
            
            logger.info("开始批量分析...")
            
            # 获取分析结果
            analysis_df = self.batch_analyze(names, delay, batch_size)
            
            # 确保 analysis_df 是 DataFrame
            if not isinstance(analysis_df, pd.DataFrame):
                logger.error("分析结果不是DataFrame，创建默认结果")
                analysis_df = pd.DataFrame()
            
            # 合并结果
            if not analysis_df.empty:
                # 将分析结果与原始数据合并
                result_df = original_df.merge(
                    analysis_df, 
                    left_on=column_name, 
                    right_on='original_name', 
                    how='left'
                )
            else:
                # 如果分析结果为空，创建默认列
                result_df = original_df.copy()
                for col in ['is_licensed', 'confidence', 'full_name', 'reason', 'api_success']:
                    result_df[col] = None
            
            # 生成输出文件名
            if output_file is None:
                name, ext = os.path.splitext(input_file)
                output_file = f"{name}_分析结果{ext}"
            
            # 保存结果
            self.save_results(result_df, output_file)
            return result_df
            
        except Exception as e:
            logger.error(f"处理 Excel 文件失败: {str(e)}")
            raise

    def save_results(self, df: pd.DataFrame, filename: str):
        # 确保必要的列存在
        required_cols = ['original_name', 'is_licensed', 'confidence', 'full_name', 'reason', 'api_success']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # 重新排列列的顺序
        analysis_cols = [col for col in required_cols if col in df.columns]
        other_cols = [col for col in df.columns if col not in required_cols]
        final_cols = analysis_cols + other_cols
        
        df = df[final_cols]
        df.to_excel(filename, index=False, engine='openpyxl')
        logger.info(f"结果已保存到: {filename}")
        self.print_statistics(df)

    def print_statistics(self, df: pd.DataFrame):
        total = len(df)
        lic = len(df[df['is_licensed'] == True]) if 'is_licensed' in df.columns else 0
        high = len(df[(df['is_licensed'] == True) & (df['confidence'] == '高')]) if 'is_licensed' in df.columns and 'confidence' in df.columns else 0
        succ = len(df[df['api_success'] == True]) if 'api_success' in df.columns else 0
        
        print(f"\n=== 分析完成 ===")
        print(f"总条数: {total}")
        if total > 0:
            print(f"持牌: {lic} ({lic/total*100:.1f}%)")
            print(f"高置信: {high}")
            print(f"成功率: {succ/total*100:.1f}%")


def main():
    API_KEY = "sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol"
    classifier = FinancialInstitutionClassifier(api_key=API_KEY)

    input_excel = "/Users/chenyaxin/Desktop/privacy/商家筛选/处理后的商家列表.xlsx"
    output_excel = "/Users/chenyaxin/Desktop/机构分析结果.xlsx"

    try:
        result_df = classifier.process_excel_file(
            input_file=input_excel,
            output_file=output_excel,
            column_name="投诉商家",
            delay=0.5,
            batch_size=20
        )
        print(f"\n全部完成！结果：{output_excel}")
    except Exception as e:
        logger.error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        print(f"处理失败: {e}")


if __name__ == "__main__":
    main()