import os
from langdetect import detect, LangDetectException
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter

# 配置：目标文件夹路径
TARGET_DIR = './'  # 可修改为你的txt文件夹路径

# 递归获取所有txt文件路径
def get_all_txt_files(folder):
    txt_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.txt'):
                txt_files.append(os.path.join(root, file))
    return txt_files

# 识别单个txt文件的语言
def detect_language(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read(1000)  # 只读取前1000字符
            if not text.strip():
                return 'empty'
            lang = detect(text)
            return lang
    except LangDetectException:
        return 'unknown'
    except Exception as e:
        return 'error'

if __name__ == '__main__':
    folder = TARGET_DIR
    txt_files = get_all_txt_files(folder)
    print(f'共检测到{len(txt_files)}个txt文件')
    lang_list = []
    for file in txt_files:
        lang = detect_language(file)
        lang_list.append(lang)
        print(f'{os.path.basename(file)}: {lang}')
    # 统计
    lang_counter = Counter(lang_list)
    df = pd.DataFrame(lang_counter.items(), columns=['Language', 'Count'])
    df = df.sort_values('Count', ascending=False)
    # 保存统计表
    df.to_csv('txt_language_statistics.csv', index=False)
    # 绘图
    plt.figure(figsize=(8,5))
    plt.bar(df['Language'], df['Count'], color='skyblue')
    plt.xlabel('Language')
    plt.ylabel('File Count')
    plt.title('Language Distribution of TXT Files')
    plt.tight_layout()
    plt.savefig('txt_language_distribution.png', dpi=150)
    plt.show()
    print('统计表已保存为 txt_language_statistics.csv，图表已保存为 txt_language_distribution.png')
