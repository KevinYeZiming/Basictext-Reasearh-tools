import os
import csv
import PyPDF2
from pathlib import Path

def pdf_to_txt(pdf_path, output_dir):
    """将PDF转换为TXT并保留格式"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            full_text = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                full_text.append(page_text.strip())
            
            # 生成TXT文件路径
            txt_filename = f"{pdf_path.stem}.txt"
            txt_path = output_dir / txt_filename
            
            # 写入TXT时保留原始换行
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write('\n'.join(full_text))
            return True
    except Exception as e:
        print(f"转换失败：{pdf_path.name} - {str(e)}")
        return False

def merge_txt_to_csv(txt_dir, csv_path):
    """合并TXT到CSV（确保单单元格存储）"""
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        # 配置CSV写入格式
        writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(["文件名", "正文内容"])
        
        processed_count = 0
        for txt_file in txt_dir.glob('*.txt'):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 处理特殊字符
                    cleaned_content = content.replace('\x00', '')  # 移除空字符
                    
                    # 写入CSV（确保整个内容在单个单元格）
                    writer.writerow([
                        f"{txt_file.stem}.pdf",  # 原始文件名
                        cleaned_content  # 完整内容作为单个字段
                    ])
                    processed_count += 1
            except Exception as e:
                print(f"读取失败：{txt_file.name} - {str(e)}")
        
        return processed_count

def main():
    # 路径配置
    source_dir = Path("/Users/ziming_ye/Downloads/抓取补充")         # PDF源目录
    txt_dir = Path("/Users/ziming_ye/Downloads/抓取转换/txt_temp")    # 临时TXT存储
    output_csv = Path("/Users/ziming_ye/Downloads/抓取转换/final.csv")# 最终输出
    
    # 创建临时目录
    txt_dir.mkdir(exist_ok=True)
    
    # 第一阶段：PDF转TXT
    print("🔄 PDF转换进行中...")
    pdf_files = list(source_dir.glob("*.pdf")) + list(source_dir.glob("*.PDF"))
    success = 0
    for pdf in pdf_files:
        if pdf_to_txt(pdf, txt_dir):
            success += 1
    print(f"✓ 转换完成：{success}/{len(pdf_files)} 个PDF成功转换")
    
    # 第二阶段：合并到CSV
    print("\n🔗 正在合并到CSV...")
    merged = merge_txt_to_csv(txt_dir, output_csv)
    print(f"✅ 合并完成：{merged} 个文件已存入 {output_csv}")
    print("提示：用Excel打开时，请确保选择UTF-8编码")

if __name__ == "__main__":
    main()