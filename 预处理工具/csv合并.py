import pandas as pd
import os

# 读取两个CSV文件（请替换为实际文件名）
file1 = "/Users/ziming_ye/Python/BERTopic/开盒挂人爬取数据集/detail_comments_2025-07-16.csv"  # 第一个CSV文件名
file2 = "/Users/ziming_ye/Python/BERTopic/开盒挂人爬取数据集/search_comments_2025-08-26.csv"  # 第二个CSV文件名

# 读取数据
df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# 合并数据并基于comment_id去重
combined_df = pd.concat([df1, df2], ignore_index=True)
deduplicated_df = combined_df.drop_duplicates(subset="comment_id", keep="first")

# 输出到源文件所在目录
output_file = "weibo_data.csv"
deduplicated_df.to_csv(output_file, index=False)

print(f"处理完成！结果已保存至：{os.path.abspath(output_file)}")