# 供应链、供应商、风险、不确定性
import pandas as pd
from gensim.models import Word2Vec


model_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/model/supplainword2vec.model'  # 保存模型的文件路径
words = ["供应链", "供应商", "风险", "不确定性"]
model = Word2Vec.load(model_path)
data = []
# def filter_similar_words(similar_words, original_word):
#     return [word for word in similar_words if original_word not in word]
for word in words:
    if word in model.wv.index_to_key:  # 检查word是否存在于模型的词汇表中
        similar_words = model.wv.most_similar(word, topn=80)
        for similar_word, similarity in similar_words:
            data.append({
                'original_word': word,
                'similar_word': similar_word,
                'similarity': similarity
            })
    else:
        print(f"Word '{word}' does not exist in the model's vocabulary. Skipping...")
df_similar_words = pd.DataFrame(data)

output_csv_path = '/Users/chenyaxin/Desktop/供应链风险指标测度/年报数据/supplychainrisk.csv'
df_similar_words.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
print(f"The similar words have been written to {output_csv_path}")


