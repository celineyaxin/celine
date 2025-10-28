import pandas as pd
import re

def extract_tech_outsourcing_questions(data_file, output_file):
    """
    直接从银行问答数据中提取与科技外包监管政策相关的提问
    
    参数:
    data_file: 银行问答数据文件路径
    output_file: 提取结果输出文件路径
    """
    
    # 读取银行问答数据
    df = pd.read_excel(data_file)
    print(f"读取到 {len(df)} 条银行问答记录")
    
    # 根据政策内容优化的关键词列表
    keywords = [
        # 政策文件相关
        '银保监办发〔2021〕141号', '141号文', '信息科技外包风险监管办法',
        '科技外包监管', '外包风险监管',
        
        # 核心概念
        '信息科技外包', '科技外包', 'IT外包', '技术服务外包',
        '外包风险', '外包风险管理', '外包监管',
        
        # 政策重点内容
        '不得外包', '不能外包的职能', '核心能力建设', '网络安全主体责任',
        '重要外包', '一般外包', '非驻场外包', '跨境外包', '关联外包', '同业外包',
        '服务提供商', '外包服务商', '第三方服务',
        
        # 管理要求
        '外包战略', '外包管理体系', '外包治理', '外包准入', '尽职调查',
        '外包合同', '服务水平协议', '外包监控', '外包评价',
        '外包审计', '外包评估', '外包退出', '退出策略',
        
        # 风险类型
        '科技能力丧失', '业务中断', '数据泄露', '数据安全', '个人信息保护',
        '资金损失', '服务水平下降', '集中度风险',
        
        # 监管要求
        '监管报告', '重大风险事件', '监管检查', '银保监会检查',
        '应急管理', '业务连续性', '灾难恢复',
        
        # 数据安全
        '重要数据', '客户个人信息', '数据跨境', '信息跨境',
        '安全保密', '网络安全', '信息安全'
    ]
    
    # 创建正则表达式模式，不区分大小写
    pattern = re.compile('|'.join(keywords), re.IGNORECASE)
    
    # 筛选包含关键词的提问
    tech_outsourcing_questions = df[df['提问内容'].apply(lambda x: bool(pattern.search(str(x))))].copy()
    
    print(f"找到 {len(tech_outsourcing_questions)} 条与科技外包监管相关的提问")
    
    # 保存提取结果
    if not tech_outsourcing_questions.empty:
        # 确保输出目录存在
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 保存到Excel文件
        tech_outsourcing_questions.to_excel(output_file, index=False)
        print(f"提取结果已保存到 {output_file}")
        
        # 打印一些示例提问
        print("\n=== 示例提问 ===")
        for i, row in tech_outsourcing_questions.head(5).iterrows():
            print(f"{row.get('年份', '未知年份')}年 {row.get('股票代码', '未知代码')}: {row['提问内容'][:100]}...")
    else:
        print("未找到与科技外包监管政策相关的提问")
    
    return tech_outsourcing_questions

# 使用示例
if __name__ == "__main__":
    # 设置参数
    data_file = "/Users/chenyaxin/Desktop/银行互动易问答数据.xlsx"  # 银行问答数据文件
    output_file = "/Users/chenyaxin/Desktop/科技外包监管相关提问.xlsx"  # 输出文件
    
    # 执行提取
    result = extract_tech_outsourcing_questions(data_file, output_file)