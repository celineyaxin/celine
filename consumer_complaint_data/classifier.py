import csv
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from gensim.models import Word2Vec
from sklearn.ensemble import RandomForestClassifier
from collections import Counter
import jieba
from sklearn.neighbors import KNeighborsClassifier

def read_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = [row['投诉内容'] for row in reader]
    return data

def load_stop_words_and_userdict(stop_words_file, userdict_file):
    with open(stop_words_file, 'r', encoding='utf-8') as file:
        stop_words = set(line.strip() for line in file)
    with open(userdict_file, 'r', encoding='utf-8') as file:
        userdict = {line.strip(): 1 for line in file}  # 假设自定义词典中的词频都为1
    return stop_words, userdict
  
def extract_features(text, model, stop_words, userdict):
    jieba.load_userdict(userdict) 
    text_lower = text.lower()
    words = jieba.cut(text_lower)
    word_freq = Counter(words)
    # 加权平均值
    # filtered_words = [word for word in words if word not in stop_words and word_freq[word] > 1]
    # vectors = [model[word] for word in filtered_words if word in model.vocab]
    # if vectors:
    #     word_weights = [word_freq[word] for word in filtered_words if word in model.vocab]
    #     weighted_sum = np.sum([np.array(vector) * weight for vector, weight in zip(vectors, word_weights)], axis=0)
    #     weighted_avg_vec = weighted_sum / np.sum(word_weights)
    #     return weighted_avg_vec
    # else:
    #     return np.zeros(model.vector_size)
    filtered_words = [word for word in words if word not in stop_words and word_freq[word] > 1 and word in model.vocab]
    vectors = [model[word] for word in filtered_words]
    if vectors:
        average_vector = np.mean(vectors, axis=0)
        return average_vector
    else:
        return np.zeros(model.vector_size)   
    
def train_and_evaluate_model(X, y, model_name, model, stop_words, userdict):
    X_features = [extract_features(text, model, stop_words, userdict) for text in X]
    model.fit(X_features, y)
    predictions = model.predict(X_features)
    accuracy = accuracy_score(y, predictions)
    print(f"{model_name} 准确率: {accuracy:.2f}")
    return model, accuracy

def save_classified_dataset(data, model, output_file_path, stop_words, userdict):
    all_features = [extract_features(text, model, stop_words, userdict) for text in data]
    predictions = model.predict(all_features)
    with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['投诉内容', 'predicted_label'])  
        for text, prediction in zip(data, predictions):
            writer.writerow([text, prediction])
def main():
    text_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/financial_complains.csv'
    loan_path="/Users/chenyaxin/Desktop/websitdata/merge_data3/loan_complaints.csv"
    word2vec_model_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/word2vec.model'
    stop_words_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/stopwords.txt'  
    userdict_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/selfdictionary.txt' 
    output_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/classified_dataset.csv'
    
    try:
        text_data = read_csv(text_file_path)
        loan_data = read_csv(loan_path)
        combined_data = text_data + loan_data
        set_loan_data = set(loan_data)
        labels = [1 if text in set_loan_data else 0 for text in combined_data]
        X_train, X_test, y_train, y_test = train_test_split(combined_data, labels, test_size=0.2, random_state=42)
        stop_words, userdict = load_stop_words_and_userdict(stop_words_file_path, userdict_file_path)
        model = Word2Vec.load(word2vec_model_path)
        models_accuracies = {}
        models = {
                '朴素贝叶斯': MultinomialNB(),
                'SVM': make_pipeline(SVC(kernel='rbf', probability=True, C=1.0, random_state=0, gamma=0.2)),
                # 'rbf'、'linear'、'poly'或'sigmoid'
                '逻辑回归': LogisticRegression(solver='liblinear', max_iter=1000),
                '随机森林': RandomForestClassifier(n_estimators=20),
                'KNN': KNeighborsClassifier(n_neighbors=3)
            }
        for name, model in models.items():
                model, accuracy = train_and_evaluate_model(X_train, y_train, name, model, stop_words)
                models_accuracies[name] = (model, accuracy)
        best_model_name, (best_model, best_accuracy) = max(models_accuracies.items(), key=lambda x: x[1][1])
        print(f"最佳模型是 {best_model_name}，准确率为: {best_accuracy:.2f}")
    
        all_data = combined_data + X_test  # 合并训练集和测试集
        all_features = [extract_features(text, model, stop_words, userdict) for text in all_data]
        best_model.predict(all_features)  
        save_classified_dataset(all_data, best_model, output_file_path, stop_words, userdict)

    except Exception as e:
        print(f"程序发生错误: {e}")

if __name__ == "__main__":
    main()
# models_accuracies = {}
# # 朴素贝叶斯分类器
# nb_clf = MultinomialNB()
# nb_clf.fit([extract_features(text, model) for text in X_train], y_train)
# nb_predictions = nb_clf.predict([extract_features(text, model) for text in X_test])
# nb_accuracy = accuracy_score(y_test, nb_predictions)
# models_accuracies['朴素贝叶斯'] = nb_clf, nb_accuracy
# print(f"朴素贝叶斯准确率: {nb_accuracy}")

# # SVM分类器
# svm_clf = make_pipeline(SVC(probability=True))
# svm_clf.fit([extract_features(text, model) for text in X_train], y_train)
# svm_predictions = svm_clf.predict([extract_features(text, model) for text in X_test])
# svm_accuracy = accuracy_score(y_test, svm_predictions)
# models_accuracies['SVM'] = svm_clf, svm_accuracy
# print(f"SVM准确率: {svm_accuracy}")

# # 逻辑回归分类器
# lr_clf = LogisticRegression(solver='liblinear', max_iter=1000)
# lr_clf.fit([extract_features(text, model) for text in X_train], y_train)
# lr_predictions = lr_clf.predict([extract_features(text, model) for text in X_test])
# lr_accuracy = accuracy_score(y_test, lr_predictions)
# models_accuracies['逻辑回归'] = lr_clf, lr_accuracy
# print(f"逻辑回归准确率: {lr_accuracy}")

# # 随机森林分类方法模型
# rf_clf = RandomForestClassifier(n_estimators=20)
# rf_clf.fit([extract_features(text, model) for text in X_train], y_train)
# rf_predictions = rf_clf.predict([extract_features(text, model) for text in X_test])
# rf_accuracy = accuracy_score(y_test, rf_predictions)
# models_accuracies['随机森林'] = rf_clf, rf_accuracy
# print(f"随机森林准确率: {lr_accuracy}")

# # KNN分类方法模型
# knn_clf = neighbors.KNeighborsClassifier() 
# knn_clf.fit([extract_features(text, model) for text in X_train], y_train)
# knn_predictions = knn_clf.predict(X_test)
# knn_accuracy = accuracy_score(y_test, knn_predictions)
# models_accuracies['KNN'] = knn_clf, knn_accuracy
# print(f"knn准确率: {lr_accuracy}")


# best_model_name, (best_model, best_accuracy) = max(models_accuracies.items(), key=lambda x: x[1][1])
# print(f"最佳模型是 {best_model_name}，准确率为: {best_accuracy}")

# # 保存最佳模型的结果到CSV文件
# output_file_path = '/Users/chenyaxin/Desktop/websitdata/merge_data3/best_model_results.csv'
# save_best_model_results(best_model, [extract_features(text, model) for text in X_test], combined_data, output_file_path)
