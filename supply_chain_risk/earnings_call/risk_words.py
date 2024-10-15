words = ["风险","不确定性","防范" ,"防患于未然","防范于未然", "防范措施", "挑战", "系统性", "不确定性", "影响",
    "压力", "不利", "复杂性", "隐患", "可能性", "考验", "危机",
    "困难", "负面影响", "汇率波动", "敞口", "不良", 
    "复杂性", "变数", "不稳定性", "难度", "负面影响", "可能性",
    "风险因素", "扰动", "压力", "风险", "变化", "复杂多变", "波动性", "波动",
    "市场风险", "投资风险", "不利因素", "多变", "不利","冲击", "不可控因素",
    "概率", "不明朗", "不可抗力", "比较复杂", "经济波动",
    "阻碍", "承压","阻力", "经济滑坡", "严峻性","动荡","汇率风险","外部环境风险"
    "滞后性", "宏观风险", "偏差", "需求变动", "差异", "不良影响", "挑战","系统性风险"]
unique_words_ordered = []
for word in words:
    if word not in unique_words_ordered:
        unique_words_ordered.append(word)
output_file_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/risk_words.txt'

with open(output_file_path, 'w', encoding='utf-8') as file:
    # 遍历列表中的每个词语
    for word in unique_words_ordered:
        # 写入词语，每个词语占一行
        file.write(word + '\n')

print(f"词语列表已写入到 {output_file_path}")

