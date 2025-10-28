# model_classifier.py
import pandas as pd
from openai import OpenAI
import time
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IncrementalComplaintClassifier:
    def __init__(self, api_key, model_name, model_alias):
        self.client = OpenAI(
            api_key=api_key,  # 修复：使用传入的api_key参数
            base_url="https://api.siliconflow.cn/v1"
        )
        self.model_name = model_name
        self.model_alias = model_alias
        
        self.prompt_template = """你是一名金融监管专家。请仔细阅读以下消费者投诉内容，并将其归入以下**唯一一个最核心、最主要的**业务环节类别：

【分类选项与定义】
- **营销宣传类**: 投诉核心是关于**广告、推销、揽客过程中**的不实或误导性信息。
  - **典型表现**: 虚假宣传、夸大收益、隐瞒风险、误导性对比、礼品诱导、承诺无法兑现的服务、使用模糊或绝对化用语。
  - **判断关键**: 问题源于**购买前**听到或看到的宣传信息。

- **定价收费类**: 投诉核心是关于**价格、费率、成本**的不透明、不公平或未经授权。
  - **典型表现**: 乱收费、隐藏费用、费率过高、未明码标价、擅自扣费、收费与服务不符。
  - **判断关键**: 争议的焦点直接指向**金额和费用**。

- **合同条款类**: 投诉核心是关于**合同文本内容本身**的公平性与清晰度。
  - **典型表现**: 不公平格式条款、霸王条款、条款模糊歧义、单方面变更合同、隐藏重要条款。
  - **判断关键**: 问题根源于白纸黑字的**合同约定**。

- **催收行为类**: 投诉核心是关于**贷后管理、债务催收过程中**的不当或违规行为。
  - **典型表现**: 恶意催收、暴力催收、骚扰式催收、泄露隐私给第三方、侮辱恐吓、冒充公检法、骚扰无关人员。
  - **适用说明**: 主要适用于银行、消费金融公司等信贷业务机构

- **客户服务类**: 投诉核心是关于**交易完成后的服务、执行或售后环节**的质量与效率。
  - **典型表现**: 理赔/兑付困难、无理拒赔、拖延处理、服务态度恶劣、泄露隐私、系统故障、业务办理效率低。

- **其他类**: 投诉内容不属于以上五类，或涉及**系统技术问题、业务流程问题、机构管理问题**等。
  - **典型表现**: 系统bug、页面无法打开、业务流程设计不合理、机构内部管理混乱、非消费者权益相关的技术问题等。
  - **判断关键**: 问题与消费者权益无直接关联，更多是技术或管理层面的问题。

【核心判断原则】
**追溯根源**：请选择投诉问题链中**最根本、最先发生**的环节。

请输出严格的JSON格式：
{{"category": "类别名称", "reason": "简要说明归类依据"}}

消费者投诉内容：
"{complaint_text}"
"""
    
    def incremental_classify(self, sample_file, output_dir, 
                           start_index=0, num_to_classify=None, save_batch_size=50, delay=1):
        """通用增量分类方法 - 支持Excel输入"""
        try:
            # 创建主输出文件夹和临时文件夹
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 创建临时文件夹用于存放过程文件
            temp_dir = output_path / "temp_files"
            temp_dir.mkdir(exist_ok=True)
            file_extension = Path(sample_file).suffix.lower()
            logging.info(f"[{self.model_alias}] 正在读取文件: {sample_file}, 格式: {file_extension}")
            if file_extension == '.csv':
                df = pd.read_csv(sample_file, encoding='utf-8')  # 如果是其他编码可以改为 'gbk'
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(sample_file, engine='openpyxl')
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")
        
            complaint_column = '发起投诉内容'
            
            # 检查必要的列
            if complaint_column not in df.columns:
                raise ValueError(f"Excel文件中必须包含'{complaint_column}'列")
            
            total_samples = len(df)
            logging.info(f"[{self.model_alias}] 总记录数: {total_samples}")
            
            # 如果没有指定数量，则处理从start_index开始的所有数据
            if num_to_classify is None:
                end_index = total_samples
            else:
                end_index = min(start_index + num_to_classify, total_samples)
            
            actual_count = end_index - start_index
            
            logging.info(f"[{self.model_alias}] 处理范围: {start_index}-{end_index-1}, 数量: {actual_count}")
            
            # 初始化分类列
            result_column = f'分类结果_{self.model_alias}'
            reason_column = f'分类理由_{self.model_alias}'
            time_column = f'分类时间_{self.model_alias}'
            
            if result_column not in df.columns:
                df[result_column] = ''
                df[reason_column] = ''
                df[time_column] = ''
            
            processed_count = 0
            batch_count = 0
            
            for i in range(start_index, end_index):
                # 跳过空内容
                if pd.isna(df.at[i, complaint_column]) or str(df.at[i, complaint_column]).strip() == '':
                    df.at[i, result_column] = '内容为空'
                    df.at[i, reason_column] = '跳过空内容'
                    df.at[i, time_column] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    continue
                
                # 如果已经分类过，跳过
                if pd.notna(df.at[i, result_column]) and df.at[i, result_column] != '':
                    logging.info(f"[{self.model_alias}] 第 {i} 条已分类，跳过")
                    continue
                
                complaint_text = str(df.at[i, complaint_column]).strip()
                result = self.classify_single_complaint(complaint_text)
                
                df.at[i, result_column] = result['category']
                df.at[i, reason_column] = result['reason']
                df.at[i, time_column] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                
                processed_count += 1
                
                # 进度提示
                if processed_count % 10 == 0:
                    current_progress = i - start_index + 1
                    logging.info(f"[{self.model_alias}] 进度: {current_progress}/{actual_count}, 已分类: {processed_count}")
                
                # 分批保存到临时文件夹
                if processed_count % save_batch_size == 0:
                    batch_count += 1
                    self._save_progress(df, temp_dir, sample_file, batch_count)
                    logging.info(f"[{self.model_alias}] 第{batch_count}批数据已保存到临时文件夹")
                
                time.sleep(delay)
            
            # 保存最终结果到主输出文件夹
            final_output = output_path / f"{Path(sample_file).stem}_{self.model_alias}_results.xlsx"
            df.to_excel(final_output, index=False, engine='openpyxl')
            
            # 保存进度信息到主输出文件夹
            progress_info = {
                'model': self.model_alias,
                'sample_file': sample_file,
                'start_index': start_index,
                'end_index': end_index,
                'total_processed': processed_count,
                'completion_time': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'next_start_index': end_index
            }
            
            progress_file = output_path / f"{Path(sample_file).stem}_{self.model_alias}_progress.json"
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_info, f, ensure_ascii=False, indent=2)
            
            logging.info(f"[{self.model_alias}] 完成! 处理了 {processed_count} 条")
            logging.info(f"[{self.model_alias}] 最终结果: {final_output}")
            logging.info(f"[{self.model_alias}] 过程文件保存在: {temp_dir}")
            logging.info(f"[{self.model_alias}] 下次可从第 {end_index} 条开始")
            
            return df, final_output, progress_info
            
        except Exception as e:
            logging.error(f"[{self.model_alias}] 分类失败: {e}")
            raise
    
    def classify_single_complaint(self, complaint_text):
        """分类单条投诉"""
        try:
            if not complaint_text or len(complaint_text.strip()) < 5:
                return {"category": "无法分类", "reason": "投诉内容过短或为空"}
            
            prompt = self.prompt_template.format(complaint_text=complaint_text)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            return self._parse_response(result)
            
        except Exception as e:
            logging.error(f"API调用失败: {e}")
            return {"category": "分类错误", "reason": f"API调用失败: {str(e)}"}
    
    def _parse_response(self, response_text):
        """解析API响应"""
        try:
            import json
            # 清理响应文本，提取JSON部分
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                
                # 验证结果格式 - 修复：添加"其他类"
                valid_categories = ["营销宣传类", "定价收费类", "合同条款类", "客户服务类", "催收行为类", "其他类"]
                if "category" in result and "reason" in result:
                    if result["category"] in valid_categories:
                        return result
                    else:
                        return {"category": "分类错误", "reason": f"返回类别不在预期范围内: {result['category']}"}
                else:
                    return {"category": "分类错误", "reason": "返回格式缺少必要字段"}
            else:
                return {"category": "分类错误", "reason": "未找到有效的JSON响应"}
                
        except json.JSONDecodeError as e:
            logging.error(f"JSON解析失败: {e}")
            return {"category": "分类错误", "reason": f"JSON解析失败: {str(e)}"}
    
    def _save_progress(self, df, output_path, sample_file, batch_count):
        """保存进度到指定文件夹"""
        file_stem = Path(sample_file).stem
        temp_output = output_path / f"{file_stem}_{self.model_alias}_batch_{batch_count}.xlsx"
        df.to_excel(temp_output, index=False, engine='openpyxl')
        logging.info(f"[{self.model_alias}] 批次保存: {temp_output}")
        
    def get_classification_progress(self, sample_file, output_dir):
        """获取分类进度"""
        try:
            progress_file = Path(output_dir) / f"{Path(sample_file).stem}_{self.model_alias}_progress.json"
            
            if progress_file.exists():
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_info = json.load(f)
                return progress_info
            else:
                return {'next_start_index': 0}
                
        except:
            return {'next_start_index': 0}
        
