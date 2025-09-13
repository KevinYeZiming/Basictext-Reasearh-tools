import docx
import jieba
from wordcloud import WordCloud
from collections import Counter
import matplotlib.pyplot as plt

def read_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def load_stopwords(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def process_text(text, stopwords):
    words = jieba.lcut(text)
    return [word for word in words if len(word) > 1 
            and word not in stopwords 
            and not word.isspace()]

def generate_wordcloud(word_freq, font_path):
    wc = WordCloud(
        font_path=font_path,
        width=1200,
        height=800,
        background_color='white',
        max_words=200
    )
    wc.generate_from_frequencies(word_freq)
    plt.figure(figsize=(12, 8))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')
    plt.show()
if __name__ == "__main__":
    # 配置参数（需要根据实际情况修改路径）
    doc_path = "/Volumes/ZimingYe/Python/input.docx"        # Word文档路径
    stopwords_path = "/Volumes/ZimingYe/Python/cn_all_stopwords.txt"  # 停用词文件路径
    font_path = "/Volumes/ZimingYe/Python/Simhei.ttf"       # 中文字体文件路径
    
    # 文本处理流程
    text = read_docx(doc_path)
    stopwords = load_stopwords(stopwords_path)
    filtered_words = process_text(text, stopwords)  # 正确在此定义变量
    
    # 词云生成
    word_counts = Counter(filtered_words)
    top_words = dict(word_counts.most_common(200))
    generate_wordcloud(top_words, font_path)
 