from gensim.models import Word2Vec


if __name__ == '__main__':
    WORD2VEC_MODEL_DIR = '/Users/chenyaxin/Desktop/供应链风险指标测度/业绩说明会数据/model/supplainword2vec.model'

    word2vec_model = Word2Vec.load(WORD2VEC_MODEL_DIR)

    while True:
        # 获取用户输入的单词
        word = input("Enter a word to find similar words (or 'quit' to stop): ")
        
        # 检查用户是否想要退出程序
        if word.lower() == 'quit':
            print("Exiting the program.")
            break
        
        # 查找并打印相似词
        try:
            sim_words = word2vec_model.wv.most_similar(word, topn=20)  # 假设我们打印每个词10个最相似的词
            print(f"The most similar words to '{word}' are: ")
            for w in sim_words:
                print(w)
        except KeyError:
            print(f"The word '{word}' was not found in the vocabulary. Please try another word.")

