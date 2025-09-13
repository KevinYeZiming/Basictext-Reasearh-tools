import pandas as pd
import os
import jieba
from gensim import corpora, models
from gensim.models import CoherenceModel
from snownlp import SnowNLP
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib import rcParams, font_manager
import numpy as np
from multiprocessing import freeze_support
import pyLDAvis.gensim_models as gensimvis # 导入 pyLDAvis 的 gensim 模块
import pyLDAvis # 导入 pyLDAvis

# 启用tqdm的pandas集成
tqdm.pandas()

# --- 可编辑配置 ---
CONFIG = {
    # 输入CSV文件路径（需包含列 content 或以 content 开头的多列）
    'input_csv_path': '/Users/ziming_ye/Python/BERTopic/开盒评论集合（6平台）.csv',
    # 输出根目录（可选）。若为None，则在输入CSV同目录下创建同名文件夹
    'output_root_dir': None,
}

# --- 全局函数和配置 ---

# 加载停用词
def load_stopwords(filepath='/Volumes/ZimingYe/Python/cn_all_stopwords.txt'):
    """加载停用词"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return set([line.strip() for line in f])

# 全局停用词变量，只加载一次
stopwords = load_stopwords()

# 中文分词函数
def tokenize(text):
    """分词，并去除停用词和单个字符"""
    return [w for w in jieba.lcut(text) if w not in stopwords and len(w.strip()) > 1]

# 计算情感得分
def sentiment_score(text):
    """计算情感得分（0到1之间，越接近1越积极）"""
    try:
        return SnowNLP(text).sentiments
    except:
        return 0.5 # 异常情况返回中性

# 扩展情感分析（分类为积极、中性、消极）
def extended_sentiment_analysis(text):
    """根据情感得分分类为 '积极', '中性', '消极'"""
    try:
        score = SnowNLP(text).sentiments
        if score > 0.7:
            return "积极"
        elif score < 0.3:
            return "消极"
        else:
            return "中性"
    except:
        return "未知"

# --- 主流程函数 ---

def prepare_output_dir(input_csv_path, output_dir=None):
    """基于输入CSV创建输出目录，若指定了output_dir则使用指定目录"""
    if output_dir:
        target_dir = output_dir
    else:
        # 直接在输入CSV的同一文件夹内创建同名子文件夹
        base_name = os.path.splitext(os.path.basename(input_csv_path))[0]
        parent_dir = os.path.dirname(input_csv_path)
        target_dir = os.path.join(parent_dir, base_name)
    
    try:
        os.makedirs(target_dir, exist_ok=True)
        print(f"📁 输出目录: {target_dir}")
        
        # 验证目录是否真的创建成功
        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            print(f"✅ 输出目录创建成功")
        else:
            print(f"❌ 输出目录创建失败: {target_dir}")
            # 尝试创建父目录
            parent = os.path.dirname(target_dir)
            if not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
                os.makedirs(target_dir, exist_ok=True)
                print(f"✅ 重新创建输出目录成功")
        
    except Exception as e:
        print(f"❌ 创建输出目录时出错: {e}")
        # 回退到当前工作目录
        target_dir = os.path.join(os.getcwd(), "LDA_输出结果")
        os.makedirs(target_dir, exist_ok=True)
        print(f"📁 使用回退目录: {target_dir}")
    
    return target_dir


def main():
    input_csv_path = CONFIG['input_csv_path']
    output_dir = CONFIG.get('output_root_dir')
    # 1. 读取数据
    print("\n📚 正在读取数据...")
    df = pd.read_csv(input_csv_path)

    # 自动检测并合并所有以 content 开头的列
    content_like_columns = [col for col in df.columns if str(col).lower().startswith('content')]
    if len(content_like_columns) == 0:
        raise ValueError("未在输入CSV中找到以 'content' 开头的列，请检查数据列名。")

    print(f"🔎 检测到用于分析的列: {content_like_columns}")

    def merge_content_columns(row):
        parts = []
        for column_name in content_like_columns:
            value = row.get(column_name)
            if pd.notna(value):
                parts.append(str(value))
        return '。'.join(parts).strip()

    df['content'] = df.apply(merge_content_columns, axis=1)
    df = df[df['content'].astype(str).str.strip() != '']  # 去除空评论
    texts = df['content'].astype(str).tolist()

    # 2. 中文分词
    print("✂️ 正在进行分词...")
    tokenized_texts = [tokenize(text) for text in tqdm(texts, desc="分词中")]

    # 3. 构建字典和语料库
    print("📖 构建字典和语料库...")
    dictionary = corpora.Dictionary(tokenized_texts)
    corpus = [dictionary.doc2bow(text) for text in tokenized_texts]


    # 4. 构建LDA模型（固定6个主题）
    print("\n🔍 正在训练LDA模型（固定6个主题）...")
    
    # 固定主题数目为6
    best_num_topics = 6
    print(f"🎯 使用固定主题数目: {best_num_topics}")
    
    # 构建LDA模型
    lda_model = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=best_num_topics,
        passes=10,
        random_state=42
    )
    print("✅ LDA模型训练完成！")
    
    # 计算并显示模型评估指标
    coherence_model = CoherenceModel(
        model=lda_model,
        texts=tokenized_texts,
        dictionary=dictionary,
        coherence='c_v'
    )
    coherence_score = coherence_model.get_coherence()
    perplexity_score = lda_model.log_perplexity(corpus)
    
    print(f"📊 模型评估指标:")
    print(f"  一致性 c_v: {coherence_score:.4f}")
    print(f"  困惑度: {perplexity_score:.2f}")
    
    # 准备输出目录
    output_base_dir = prepare_output_dir(input_csv_path, output_dir)

    print("\n🧠 LDA主题关键词展示：")
    for i, topic in lda_model.show_topics(num_words=10, formatted=True):
        print(f"主题 {i}: {topic}")

    # 5. 情感分析
    print("\n💭 正在进行情感分析...")
    df['sentiment'] = df['content'].progress_apply(sentiment_score)
    df['sentiment_category'] = df['content'].progress_apply(extended_sentiment_analysis)

    # 6. 每条评论归类到主主题
    print("\n📊 正在进行主题分类...")
    def get_main_topic(text_content):
        # 使用之前定义的tokenize函数
        tokens = tokenize(text_content)
        bow = dictionary.doc2bow(tokens)
        topics = lda_model.get_document_topics(bow)
        # 返回概率最大的主题编号
        return max(topics, key=lambda x: x[1])[0] if topics else -1

    df['topic'] = df['content'].progress_apply(get_main_topic)

    # 确保情感主题数量与 LDA 主题数量一致 (过滤未归类的评论)
    original_comments = len(df)
    df = df[df['topic'] != -1]
    print(f"🔍 过滤掉未归类主题的评论，剩余评论数量: {len(df)} (原:{original_comments})")

    # 7. 按主题汇总情感得分
    summary = df.groupby('topic')['sentiment'].agg(['mean', 'count']).reset_index()
    summary.columns = ['主题', '平均情感', '评论数量']
    print("\n📊 每个主题的平均情感得分：")
    print(summary)

    # 8. 可视化情感分布 (保持原样)
    print("\n🔍 正在计算情感分布并可视化...")
    sentiment_distribution = df.groupby(['topic', 'sentiment_category']).size().reset_index(name='count')
    print("\n📊 每个主题的情感类别分布：")
    print(sentiment_distribution)

    # 设置中文字体
    try:
        # 尝试多种中文字体路径
        font_paths = [
            '/Users/ziming_ye/Python/Simhei.ttf',
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc'
        ]
        
        font_set = False
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    font_manager.fontManager.addfont(font_path)
                    rcParams['font.sans-serif'] = ['SimHei', 'PingFang SC', 'STHeiti', 'Arial Unicode MS']
                    font_set = True
                    print(f"✅ 使用中文字体: {font_path}")
                    break
                except:
                    continue
        
        if not font_set:
            # 使用系统默认中文字体
            rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Arial Unicode MS', 'SimHei']
            print("⚠️ 使用系统默认中文字体")
            
    except Exception as e:
        # 回退到系统默认中文字体
        rcParams['font.sans-serif'] = ['PingFang SC', 'STHeiti', 'Arial Unicode MS', 'SimHei']
        print(f"⚠️ 字体设置失败，使用默认字体: {e}")
    
    rcParams['axes.unicode_minus'] = False

    # 学术论文友好且色盲安全的 Okabe–Ito 配色
    # 积极: 绿色  中性: 灰色  消极: 朱红
    morandi_colors = {
        '积极': '#009E73',
        '中性': '#7F7F7F',
        '消极': '#D55E00'
    }

    # 计算每个主题的情感分布比例
    topic_sentiments = {}
    for topic in sorted(sentiment_distribution['topic'].unique()): # 确保主题顺序
        topic_data = sentiment_distribution[sentiment_distribution['topic'] == topic]
        total = topic_data['count'].sum()
        proportions = {}
        for sentiment in ['积极', '中性', '消极']:
            count = topic_data[topic_data['sentiment_category'] == sentiment]['count'].values
            proportions[sentiment] = count[0] / total if len(count) > 0 else 0
        topic_sentiments[topic] = proportions

    # 绘制堆叠柱状图
    plt.figure(figsize=(12, 7))
    x = list(topic_sentiments.keys())
    bottom = np.zeros(len(x))

    for sentiment in ['积极', '中性', '消极']:
        proportions = [topic_sentiments[topic][sentiment] for topic in x]
        plt.bar(x, proportions, bottom=bottom,
                label=sentiment,
                color=morandi_colors[sentiment],
                alpha=0.85,
                width=0.6)
        bottom += proportions

    # 设置图表样式
    plt.xlabel('主题编号', fontsize=11)
    plt.ylabel('比例', fontsize=11)
    plt.title('各主题的情感类别比例分布', fontsize=13, pad=15)

    # 自定义图例样式
    legend = plt.legend(title='情感类别', title_fontsize=11, fontsize=10,
                        bbox_to_anchor=(1.02, 1), loc='upper left')
    legend.get_frame().set_alpha(0.9)
    legend.get_frame().set_edgecolor('#E5E5E5')

    # 设置网格线和刻度
    plt.grid(True, linestyle='--', alpha=0.3, color='#666666')
    plt.ylim(0, 1.0)
    plt.yticks([i/10 for i in range(0, 11)], [f'{i*10}%' for i in range(0, 11)])

    # 设置背景色
    plt.gca().set_facecolor('#FAFAFA')
    plt.gcf().patch.set_facecolor('#FAFAFA')

    # 调整布局
    plt.tight_layout()
    plt.subplots_adjust(right=0.85)

    # 添加数值标签
    for i in x:
        total = 0
        for sentiment in ['积极', '中性', '消极']:
            value = topic_sentiments[i][sentiment]
            if value > 0.05:
                plt.text(i, total + value/2, f'{value:.0%}',
                        ha='center', va='center',
                        color='white', fontsize=9, fontweight='bold')
            total += value

    # 保存图表
    stacked_png_path = os.path.join(output_base_dir, '主题情感堆叠分布.png')
    plt.savefig(stacked_png_path,
                dpi=300,
                bbox_inches='tight',
                facecolor='#FAFAFA')
    plt.show()
    print(f"✅ 主题情感堆叠分布图已保存: {stacked_png_path}")

    # 9. 生成交互式LDA图
    print("\n🔍 正在生成 LDA 的 HTML 图...")
    # pyLDAvis.enable_notebook() # Only if running in a Jupyter Notebook
    lda_vis = gensimvis.prepare(lda_model, corpus, dictionary, sort_topics=False)
    html_path = os.path.join(output_base_dir, 'lda_topics_visualization.html')
    pyLDAvis.save_html(lda_vis, html_path)
    print(f"✅ LDA 的 HTML 图已保存为: {html_path}")

    # 10. 数据保存
    result_csv_path = os.path.join(output_base_dir, '情感主题分析扩展结果.csv')
    df.to_csv(result_csv_path, index=False, encoding='utf-8-sig')
    print(f"✅ 分析结果已保存: {result_csv_path}")

    # 11. 生成单独的情感分类表 (基于过滤后的数据)
    print("\n🔍 正在生成单独的情感分类表...")
    standalone_sentiment_distribution = df.groupby(['sentiment_category']).size().reset_index(name='count')
    print("\n📊 单独的情感分类分布：")
    print(standalone_sentiment_distribution)

    # 保存单独的情感分类表
    standalone_csv_path = os.path.join(output_base_dir, '单独情感分类结果.csv')
    standalone_sentiment_distribution.to_csv(standalone_csv_path, index=False, encoding='utf-8-sig')
    print(f"✅ 单独情感分类结果已保存: {standalone_csv_path}")

    # 12. 按主题保存评论文本
    print("\n🔍 正在按主题保存评论文本...")
    for topic_id in sorted(df['topic'].unique()):
        topic_comments = df[df['topic'] == topic_id][['content', 'sentiment', 'sentiment_category']].copy()
        topic_csv_path = os.path.join(output_base_dir, f'主题{topic_id}_评论文本.csv')
        topic_comments.to_csv(topic_csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ 主题{topic_id}的{len(topic_comments)}条评论已保存: {topic_csv_path}")
    
    # 13. 生成主题汇总表（包含每个主题的关键词和评论数量）
    print("\n🔍 正在生成主题汇总表...")
    topic_summary = []
    for topic_id in sorted(df['topic'].unique()):
        topic_comments = df[df['topic'] == topic_id]
        topic_words = lda_model.show_topics(num_topics=best_num_topics, formatted=False)[topic_id]
        top_words = ', '.join([word for word, prob in topic_words[1][:5]])  # 前5个关键词
        
        topic_summary.append({
            '主题编号': topic_id,
            '关键词': top_words,
            '评论数量': len(topic_comments),
            '平均情感得分': topic_comments['sentiment'].mean(),
            '积极评论数': len(topic_comments[topic_comments['sentiment_category'] == '积极']),
            '中性评论数': len(topic_comments[topic_comments['sentiment_category'] == '中性']),
            '消极评论数': len(topic_comments[topic_comments['sentiment_category'] == '消极'])
        })
    
    topic_summary_df = pd.DataFrame(topic_summary)
    topic_summary_path = os.path.join(output_base_dir, '主题汇总表.csv')
    topic_summary_df.to_csv(topic_summary_path, index=False, encoding='utf-8-sig')
    print(f"✅ 主题汇总表已保存: {topic_summary_path}")
    print("\n📊 主题汇总表预览：")
    print(topic_summary_df)

if __name__ == '__main__':
    freeze_support() # 用于在Windows多进程环境下防止递归创建进程
    main()