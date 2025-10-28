from model_classifier import IncrementalComplaintClassifier

# 直接使用您提供的API密钥和文件路径
qwen_classifier = IncrementalComplaintClassifier(
    api_key="sk-yyxiyzecigbawpjbazgtsvjmvddgymezvclcbwuslrsmogol",
    model_name="Qwen/Qwen3-32B", 
    model_alias="qwen"
)

# 直接运行分类
result_df, final_output, progress_info = qwen_classifier.incremental_classify(
    sample_file="/Users/chenyaxin/Desktop/投诉数据_一级样本_10000条.csv",
    output_dir="/Users/chenyaxin/Desktop/classification_results",
    start_index=5000,
    num_to_classify=2000,  
    save_batch_size=50,
    delay=1
)

print("Qwen分类完成！")
print(f"结果文件: {final_output}")