from miku_ai import get_wexin_article
import asyncio
import csv

# 存储已爬取的 URL，用于去重
seen_urls = set()

async def main():
    query = "开盒挂人"
    articles = await get_wexin_article(query, top_num=20)
    
    # 打开 CSV 文件，准备写入数据
    with open('articles.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # 写入表头（如果文件为空）
        if file.tell() == 0:
            writer.writerow(['标题', 'URL', '来源', '日期'])
        
        for article in articles:
            # 检查 URL 是否已存在
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                # 写入数据
                writer.writerow([article['title'], article['url'], article['source'], article['date']])
                print("标题：", article['title'])
                print("URL：", article['url'])
                print("来源：", article['source'])
                print("日期：", article['date'])
                print("-" * 50)

asyncio.run(main())