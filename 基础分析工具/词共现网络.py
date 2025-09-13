import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import jieba
import matplotlib
from matplotlib import font_manager

# 设置 matplotlib 使用指定路径的 SimHei 字体
font_path = '/Users/ziming_ye/Python/Simhei.ttf'
font = font_manager.FontProperties(fname=font_path)
matplotlib.rcParams['font.sans-serif'] = font.get_name()
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


# 获取所有词并计算频率
# 读取停用词
with open('/Volumes/ZimingYe/Python/cn_all_stopwords.txt', 'r', encoding='utf-8') as f:
    stop_words = set([line.strip() for line in f])

# 读取CSV文件并预处理
df = pd.read_csv('/Volumes/ZimingYe/非学术论文写作/A项目/上海科技馆/豆瓣 - 肖申克.csv')
df = df.dropna(subset=['内容'])       # 去除空评论
texts = df['内容'].astype(str).tolist()

# 将'text'列添加到DataFrame中
df['text'] = texts
all_words = []
for text in df['text']:
    words = text.split()  # 假设文本已经预处理过
    all_words.extend(words)

# 去除停用词
# 使用 jieba 分词并去除停用词
filtered_texts = []
for text in texts:
    words = jieba.lcut(text)  # 使用 jieba 分词
    filtered_words = [word for word in words if word not in stop_words]
    filtered_texts.append(' '.join(filtered_words))

# 更新 DataFrame 中的 'text' 列
df['text'] = filtered_texts

# 确保停用词过滤正确
all_words = []
for text in filtered_texts:  # 使用过滤后的文本
    words = text.split()
    all_words.extend(words)

# 获取前30个高频词
target_words = [word for word, count in Counter(all_words).most_common(30)]

# 创建空的共现矩阵
cooccurrence_matrix = {word1: {word2: 0 for word2 in target_words} for word1 in target_words}

# 计算共现频率
for text in filtered_texts:  # 使用过滤后的文本
    words = text.split()
    for i, word1 in enumerate(words):
        if word1 in target_words:
            for word2 in words[max(0, i-5):i+6]:  # 考虑词的上下文窗口
                if word2 in target_words and word1 != word2:
                    cooccurrence_matrix[word1][word2] += 1

# 转换共现矩阵为CSV格式
edges = []
for word1, connections in cooccurrence_matrix.items():
    for word2, count in connections.items():
        if count > 0:
            edges.append([word1, word2, count])

# 保存为CSV文件
output_path = '/Users/ziming_ye/Python/网页数据采集-数据新闻教材/top30_cooccurrence.csv'
import csv
with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Source', 'Target', 'Weight'])
    writer.writerows(edges)

print(f"共现数据已保存到 {output_path}")

# 归一化边权重
max_weight = max([count for connections in cooccurrence_matrix.values() for count in connections.values()])
normalized_edges = []
for word1, connections in cooccurrence_matrix.items():
    for word2, count in connections.items():
        if count > 0:
            normalized_weight = count / max_weight  # 归一化处理
            normalized_edges.append([word1, word2, normalized_weight])

# 保存归一化结果为CSV文件
output_path = '/Users/ziming_ye/Python/网页数据采集-数据新闻教材/top30_cooccurrence_normalized.csv'
import csv
with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Source', 'Target', 'Normalized Weight'])
    writer.writerows(normalized_edges)

print(f"归一化共现数据已保存到 {output_path}")

# 保存源节点为CSV文件
source_nodes_path = '/Users/ziming_ye/Python/网页数据采集-数据新闻教材/source_nodes.csv'
with open(source_nodes_path, 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Source'])
    writer.writerows([[word] for word in target_words])

print(f"源节点数据已保存到 {source_nodes_path}")

# 保存边节点为CSV文件
edges_path = '/Users/ziming_ye/Python/网页数据采集-数据新闻教材/edges.csv'
with open(edges_path, 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Source', 'Target', 'Weight'])
    writer.writerows(edges)

print(f"边节点数据已保存到 {edges_path}")