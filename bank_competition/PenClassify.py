import pandas as pd
import json
import time
import os
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key="YOUR_API_KEY_FROM_CLOUD_SILICONFLOW_CN",
    base_url="https://api.siliconflow.cn/v1"
)

def classify_internal_control_penalty(penalty_text):
    """
    识别内控相关的行政处罚，如果是内控类则进一步分类子类别
    """
    classification_prompt = """
请严格判断以下银行保险机构的行政处罚事实是否属于"内控相关处罚"。

内控相关处罚的定义：涉及内部管理制度、业务流程、系统建设、人员管理、监督机制等基础管理问题的处罚。

如果不属于内控相关处罚，请直接返回"非内控类"。
如果属于内控相关处罚，请进一步分类到具体子类别：

内控子类别分类：
1. "制度流程类": 内控制度不健全、业务流程不规范、授权体系混乱、岗位职责不清、审批流程缺陷
2. "人员管理类": 员工管理不到位、培训机制缺失、考核制度不完善、资质管理不规范、行为监督缺失
3. "系统监督类": 信息系统缺陷、风险监控缺失、内部审计不到位、自查自纠不落实、数据管理不规范
4. "合规管理类": 合规管理架构不完善、风险管理体系缺陷、监管要求执行不到位、消费者权益保护机制缺失

不属于内控相关处罚的情况（直接返回"非内控类"）：
- 直接的销售误导、虚假宣传、欺诈行为
- 具体的不当收费、拒绝理赔等直接侵害行为
- 单纯的信息披露不充分（除非涉及信息披露制度缺失）
- 具体的产品设计问题、费率问题等业务操作

请严格判断，只返回JSON格式：
{
    "is_internal_control": true/false,
    "subcategory": "制度流程类|人员管理类|系统监督类|合规管理类|非内控类",
    "confidence": "高|中|低",
    "reason": "简要判断理由"
}

处罚事实：{penalty_text}
"""
    
    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {"role": "system", "content": "你是一个专业的金融监管分析专家。先判断是否内控处罚，只有内控处罚才进一步分类子类别。"},
                {"role": "user", "content": classification_prompt.format(penalty_text=penalty_text)}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        result = response.choices[0].message.content.strip()
        
        try:
            classification_result = json.loads(result)
            # 确保逻辑一致性：如果subcategory是"非内控类"，is_internal_control应该为false
            if classification_result.get('subcategory') == '非内控类':
                classification_result['is_internal_control'] = False
            elif classification_result.get('is_internal_control') == False:
                classification_result['subcategory'] = '非内控类'
            return classification_result
        except json.JSONDecodeError:
            return {
                "is_internal_control": False, 
                "subcategory": "非内控类", 
                "confidence": "低", 
                "reason": "解析错误"
            }
            
    except Exception as e:
        print(f"API调用错误: {e}")
        return {
            "is_internal_control": False, 
            "subcategory": "非内控类", 
            "confidence": "低", 
            "reason": f"API错误: {str(e)}"
        }

def load_existing_results(output_file):
    """
    加载已存在的结果文件，用于断点续传
    """
    if os.path.exists(output_file):
        existing_df = pd.read_excel(output_file)
        print(f"找到现有结果文件，已处理 {len(existing_df)} 条记录")
        return existing_df
    else:
        return None

def process_data_in_batches(input_file, output_file, text_column='处罚事实', 
                          batch_size=20, delay=1, start_from=0):
    """
    分批处理数据并实时保存
    """
    # 读取输入数据
    df = pd.read_excel(input_file)
    total_records = len(df)
    print(f"总共需要处理 {total_records} 条记录")
    
    # 尝试加载现有结果
    existing_results = load_existing_results(output_file)
    
    if existing_results is not None:
        # 断点续传：找出未处理的记录
        processed_indices = set(existing_results.index)
        all_indices = set(df.index)
        remaining_indices = sorted(list(all_indices - processed_indices))
        print(f"发现 {len(remaining_indices)} 条未处理记录，从第 {remaining_indices[0] if remaining_indices else '完成'} 条开始")
        
        if not remaining_indices:
            print("所有记录已处理完成！")
            return existing_results
            
        # 合并现有结果和剩余数据
        result_df = existing_results
        indices_to_process = remaining_indices
    else:
        # 全新处理
        result_df = pd.DataFrame()
        indices_to_process = sorted(df.index)
        print(f"开始全新处理，从第 {start_from} 条开始")
    
    # 分批处理
    for batch_start in range(0, len(indices_to_process), batch_size):
        batch_end = min(batch_start + batch_size, len(indices_to_process))
        batch_indices = indices_to_process[batch_start:batch_end]
        
        print(f"\n正在处理批次 {batch_start//batch_size + 1}: 记录 {batch_start}-{batch_end}")
        
        batch_results = []
        for idx in batch_indices:
            penalty_text = df.loc[idx, text_column]
            
            # 调用分类函数
            result = classify_internal_control_penalty(str(penalty_text))
            
            # 构建结果行
            result_row = {
                '原始索引': idx,
                '处罚事实': penalty_text,
                '是否内控处罚': result.get('is_internal_control', False),
                '内控子类别': result.get('subcategory', '非内控类'),
                '内控判断置信度': result.get('confidence', '低'),
                '内控判断理由': result.get('reason', '')
            }
            
            # 添加原始数据的所有列
            for col in df.columns:
                result_row[col] = df.loc[idx, col]
            
            batch_results.append(result_row)
            
            # 显示进度
            text_preview = str(penalty_text)[:50] + "..." if len(str(penalty_text)) > 50 else str(penalty_text)
            is_internal = result.get('is_internal_control', False)
            subcategory = result.get('subcategory', '非内控类')
            status = f"内控[{subcategory}]" if is_internal else "非内控"
            print(f"  [{idx}] {status} | {text_preview}")
            
            # 延迟避免API限制
            time.sleep(delay)
        
        # 将本批次结果转换为DataFrame
        batch_df = pd.DataFrame(batch_results)
        
        # 合并到总结果
        if len(result_df) == 0:
            result_df = batch_df
        else:
            result_df = pd.concat([result_df, batch_df], ignore_index=True)
        
        # 实时保存到Excel
        result_df.to_excel(output_file, index=False)
        print(f"✅ 批次 {batch_start//batch_size + 1} 完成，已保存到 {output_file}")
        
        # 显示当前统计
        internal_count = result_df['是否内控处罚'].sum()
        if internal_count > 0:
            subcategory_stats = result_df[result_df['是否内控处罚'] == True]['内控子类别'].value_counts()
            print(f"📊 当前统计: 内控处罚 {internal_count}/{len(result_df)} ({internal_count/len(result_df):.1%})")
            print("内控子类别分布:")
            for subcat, count in subcategory_stats.items():
                print(f"  {subcat}: {count}条")
        else:
            print(f"📊 当前统计: 内控处罚 {internal_count}/{len(result_df)} ({internal_count/len(result_df):.1%})")
    
    return result_df

def extract_internal_control_records(result_df, output_file):
    """
    从完整结果中提取所有内控相关处罚记录
    """
    internal_df = result_df[result_df['是否内控处罚'] == True].copy()
    
    if len(internal_df) > 0:
        internal_output_file = output_file.replace('.xlsx', '_仅内控处罚.xlsx')
        internal_df.to_excel(internal_output_file, index=False)
        print(f"✅ 已提取 {len(internal_df)} 条内控处罚记录到: {internal_output_file}")
        
        # 内控子类别详细统计
        print("\n内控处罚子类别详细统计:")
        subcategory_stats = internal_df['内控子类别'].value_counts()
        for subcat, count in subcategory_stats.items():
            percentage = count / len(internal_df) * 100
            print(f"  {subcat}: {count}条 ({percentage:.1f}%)")
            
        return internal_df
    else:
        print("⚠️ 没有找到内控相关处罚记录")
        return None

def analyze_results(result_df):
    """
    分析分类结果并生成统计报告
    """
    print("\n" + "="*60)
    print("📈 分类结果详细分析")
    print("="*60)
    
    total_records = len(result_df)
    internal_count = result_df['是否内控处罚'].sum()
    
    print(f"总记录数: {total_records}")
    print(f"内控处罚数量: {internal_count} ({internal_count/total_records:.1%})")
    print(f"非内控处罚数量: {total_records - internal_count} ({(total_records - internal_count)/total_records:.1%})")
    
    # 内控子类别分析
    internal_df = result_df[result_df['是否内控处罚'] == True]
    if len(internal_df) > 0:
        print(f"\n内控处罚子类别分布:")
        subcategory_stats = internal_df['内控子类别'].value_counts()
        for subcat, count in subcategory_stats.items():
            percentage = count / len(internal_df) * 100
            print(f"  {subcat}: {count}条 ({percentage:.1f}%)")
    
    # 置信度分析
    print(f"\n置信度分布:")
    confidence_stats = result_df['内控判断置信度'].value_counts()
    for conf, count in confidence_stats.items():
        print(f"  {conf}: {count}条 ({count/total_records:.1%})")

def main():
    # 文件路径配置
    input_file = "/Users/chenyaxin/Desktop/2020-2024Q1行政处罚记录.xlsx"
    output_file = "/Users/chenyaxin/Desktop/行政处罚分类结果.xlsx"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：输入文件不存在 {input_file}")
        return
    
    print("=== 开始行政处罚分类处理 ===")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    try:
        # 分批处理数据
        final_result = process_data_in_batches(
            input_file=input_file,
            output_file=output_file,
            text_column='处罚事实',
            batch_size=10,
            delay=1,
            start_from=0
        )
        
        # 生成详细分析报告
        analyze_results(final_result)
        
        # 提取内控相关处罚记录
        internal_df = extract_internal_control_records(final_result, output_file)
        
        print(f"\n🎉 处理完成！")
        print(f"完整结果已保存到: {output_file}")
        if internal_df is not None:
            print(f"内控处罚记录已单独保存")
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        print("程序可以在下次运行时自动从断点继续")

# 快速测试函数
def quick_test():
    """
    快速测试分类逻辑
    """
    test_cases = [
        "内控制度不健全，业务流程不规范",  # 应该是制度流程类
        "销售误导，虚假宣传产品收益",      # 应该是非内控类
        "内部审计缺失，风险监控不到位",     # 应该是系统监督类
        "员工管理不规范，培训机制缺失",     # 应该是人员管理类
        "合规管理架构不完善",             # 应该是合规管理类
        "不当收取手续费，损害消费者权益"   # 应该是非内控类
    ]
    
    print("分类逻辑测试:\n")
    for i, text in enumerate(test_cases):
        print(f"测试案例 {i+1}: {text}")
        result = classify_internal_control_penalty(text)
        print(f"是否内控: {result.get('is_internal_control', False)}")
        print(f"子类别: {result.get('subcategory', '非内控类')}")
        print(f"置信度: {result.get('confidence', '低')}")
        print(f"理由: {result.get('reason', '')}\n")
        time.sleep(1)

if __name__ == "__main__":
    # 先运行快速测试验证分类效果
    print("=== 分类逻辑测试 ===")
    quick_test()
    
    # 确认测试效果后，取消注释运行主处理程序
    # main()