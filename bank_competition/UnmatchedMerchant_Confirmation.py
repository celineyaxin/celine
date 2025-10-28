import pandas as pd
import os
import glob

def strict_string_comparison(csv_folder, target_company, company_column='投诉对象'):
    """
    严格的字符串比较，考虑所有可能的空格情况
    """
    print(f"严格检查字符串: '{target_company}'")
    print("=" * 60)
    
    csv_files = glob.glob(os.path.join(csv_folder, "*.csv"))
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            if company_column not in df.columns:
                continue
                
            companies = df[company_column].dropna().astype(str)
            
            # 检查所有可能的空格情况
            for company in companies:
                # 原始比较
                if company == target_company:
                    print(f"✅ 找到完全匹配: '{company}'")
                    return True
                
                # 去除所有空格后比较
                if company.replace(" ", "") == target_company.replace(" ", ""):
                    print(f"⚠️  去除空格后匹配: '{company}' -> '{company.replace(' ', '')}'")
                    return True
                    
                # 去除所有空白字符（包括换行符、制表符等）
                import re
                cleaned_company = re.sub(r'\s+', '', company)
                cleaned_target = re.sub(r'\s+', '', target_company)
                if cleaned_company == cleaned_target:
                    print(f"⚠️  去除所有空白后匹配: '{company}' -> '{cleaned_company}'")
                    return True
                    
        except Exception as e:
            continue
    
    print("❌ 即使考虑所有空格情况，仍然没有找到匹配")
    return False

# 执行严格检查
csv_folder = "/Users/chenyaxin/Desktop/InternetTourismConvention/原始数据处理"
target_company = "中国人寿财险专项服务"

strict_string_comparison(csv_folder, target_company)