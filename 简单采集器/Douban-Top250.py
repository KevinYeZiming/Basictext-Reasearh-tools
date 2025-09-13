import requests
from bs4 import BeautifulSoup
import csv
import time
import re

# 请求头设置
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def get_movies():
    # 创建CSV文件
    with open('douban_top250.csv', 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['排名', '电影名称', '评分', '导演', '主演', '年份', '国家', '类型', '简介'])

        # 分页爬取（每页25条，共10页）
        for i in range(0, 250, 25):
            url = f'https://movie.douban.com/top250?start={i}'
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 解析每个电影条目
            for item in soup.find_all('div', class_='item'):
                index = item.find('em').text  # 排名
                title = item.find('span', class_='title').text  # 中文标题
                rating = item.find('span', class_='rating_num').text  # 评分
                
                # 处理包含多个信息的bd段落
                bd = item.find('div', class_='bd')
                info = bd.find('p').text.strip()
                info_parts = info.split('\n')
                
                # 提取导演和主演信息
                director_actors = info_parts[0].strip().split('   ')
                director = director_actors[0].replace('导演: ', '')
                actors = director_actors[1].replace('主演: ', '') if len(director_actors) > 1 else ''
                
                # 提取年份、国家和类型
                misc_info = re.search(r'(\d+) / (.*?) / (.*)', info_parts[1].strip())
                year = misc_info.group(1) if misc_info else ''
                country = misc_info.group(2) if misc_info else ''
                genre = misc_info.group(3) if misc_info else ''
                
                # 处理可能不存在的简介
                quote = item.find('span', class_='inq')
                quote = quote.text if quote else ''

                # 写入数据
                writer.writerow([index, title, rating, director, actors, year, country, genre, quote])

            print(f'已爬取第 {i//25+1} 页数据')
            time.sleep(2)  # 添加延迟防止被封

if __name__ == '__main__':
    get_movies()
    print('数据爬取完成！')