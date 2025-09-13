import os
import re
import argparse
from pathlib import Path

# 定义过滤正则
error_pattern = re.compile(
    r'(错误|失败|无法访问|未找到|找不到|Not\s*Found|Sorry|抱歉|404|403|405|500|502|503|504|'
    r'网页内容提取失败|网页抓取失败|内容为空|empty content|no content|'
    r'请稍等|Loading|Service Unavailable|您的浏览器|您的浏览器版本过低|出错啦|The request|This site|'
    r'Access Denied|digital nhs|De opgevraagde|BackWelcome|将您重定向的次数过多|'
    r'julkaisut|Tieto|Chair Change|すべての|Diese Seite|Sitio de Seguridad|'
    r'该操作已触发系统访问防护规则|找不到您要的页面|文件下载请输入文件|'
    r'您访问的页面不存在或已删除|共用公网IP地址触发系统访问防护规则|返回首页|'
    r'Skip content|We couldn[’\'`]?t find page|Perhaps searching)',
    re.IGNORECASE
)

def check_and_delete_error_files(folder_path, min_bytes=10, min_lines=1, min_chars=10, max_line_length=2000):
    """
    检查指定文件夹中的所有txt文件，删除以下类型的文件：
    1. 文件开头第一段包含常见网页提取失败、各类语言的错误提示、“网页内容提取为空”、常见等待提示等
    2. 空文件或内容极少（如小于min_bytes字节或小于min_lines行，或内容极短）
    3. 全部内容为标点、全是数字、全是URL、全是乱码等
    # 4. 行长度极大（如超过max_line_length），疑似异常内容（已禁用此项）
    # 5. 全为重复行的文件（已禁用）
    """
    url_pattern = re.compile(r'^(https?://|www\.)')
    punct_pattern = re.compile(r'^[\W_]+$')
    digit_pattern = re.compile(r'^\d+$')
    garbled_pattern = re.compile(r'^[\x00-\x1f\x7f-\xff]+$')

    deleted_files = []
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"错误: 文件夹 '{folder_path}' 不存在")
        return deleted_files

    txt_files = list(folder.glob('**/*.txt'))
    total_files = len(txt_files)
    print(f"开始检查 {total_files} 个txt文件...")

    for file_path in txt_files:
        try:
            # 1. 删除空文件或极小文件
            if os.path.getsize(file_path) < min_bytes:
                os.remove(file_path)
                deleted_files.append(str(file_path))
                print(f"已删除空文件或极小文件: {file_path}")
                continue

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = [l.strip() for l in file if l.strip()]
                # 2. 删除行数极少的文件
                if len(lines) < min_lines:
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                    print(f"已删除内容过少的文件: {file_path}")
                    continue
                # 3. 删除内容极短的文件
                content = ''.join(lines)
                if len(content) < min_chars:
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                    print(f"已删除内容极短的文件: {file_path}")
                    continue
                # 4. 删除全部为标点、数字、URL、乱码的文件
                if all(punct_pattern.match(l) for l in lines):
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                    print(f"已删除全为标点的文件: {file_path}")
                    continue
                if all(digit_pattern.match(l) for l in lines):
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                    print(f"已删除全为数字的文件: {file_path}")
                    continue
                if all(url_pattern.match(l) for l in lines):
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                    print(f"已删除全为URL的文件: {file_path}")
                    continue
                if all(garbled_pattern.match(l) for l in lines):
                    os.remove(file_path)
                    deleted_files.append(str(file_path))
                    print(f"已删除全为乱码的文件: {file_path}")
                    continue
                # 5. 删除行长度极大的文件（已禁用）
                # if any(len(l) > max_line_length for l in lines):
                #     os.remove(file_path)
                #     deleted_files.append(str(file_path))
                #     print(f"已删除存在超长行的文件: {file_path}")
                #     continue
                # 6. 删除全为重复行的文件（已禁用）
                # if len(set(lines)) == 1:
                #     os.remove(file_path)
                #     deleted_files.append(str(file_path))
                #     print(f"已删除全为重复行的文件: {file_path}")
                #     continue
                # 7. 只读取第一段（第一个非空段落）
                first_para = lines[0] if lines else ""
            # 8. 删除包含错误提示或内容极短的文件
            if error_pattern.search(first_para):
                os.remove(file_path)
                deleted_files.append(str(file_path))
                print(f"已删除包含错误提示的文件: {file_path}")
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")

    print(f"检查完成。共删除了 {len(deleted_files)} 个不合格文件。")
    return deleted_files

def merge_lines_by_punctuation(file_path):
    """
    读取txt文件，将非标点结尾的换行合并，按句号、问号、感叹号等断句，去除无意义换行。
    """
    import re
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    # 合并非标点结尾的换行
    # 先将所有换行替换为特殊标记
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # 只保留句末标点后的换行，其余换行替换为空格
    text = re.sub(r'(?<![。！？.!?])\n+', '', text)  # 非句末标点后的换行去掉
    text = re.sub(r'([。！？.!?])\n+', r'\1\n', text)  # 句末标点后的换行保留
    # 去除多余空行
    text = re.sub(r'\n{2,}', '\n', text)
    # 去除首尾空白
    text = text.strip()
    # 可选：按段落再分割合并
    # paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    # text = '\n'.join(paragraphs)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

def main():
    parser = argparse.ArgumentParser(description='检查并删除包含HTTP错误状态码、空文件或内容过少的txt文件')
    parser.add_argument('folder', help='要检查的文件夹路径')
    parser.add_argument('--min-bytes', type=int, default=10, help='最小文件字节数，低于此值将被删除')
    parser.add_argument('--min-lines', type=int, default=1, help='最小有效行数，低于此值将被删除')
    parser.add_argument('--min-chars', type=int, default=10, help='最小字符数，低于此值将被删除')
    parser.add_argument('--max-line-length', type=int, default=2000, help='最大行长度，超过此值的文件将被删除')
    parser.add_argument('--dry-run', action='store_true', help='仅检查不删除文件')
    args = parser.parse_args()

    if args.dry_run:
        print("【仅检查模式】将只显示包含错误的文件，不会实际删除")
        folder = Path(args.folder)
        if not folder.is_dir():
            print(f"错误: 文件夹 '{args.folder}' 不存在")
            return
        txt_files = list(folder.glob('**/*.txt'))
        total_files = len(txt_files)
        error_files = []
        print(f"开始检查 {total_files} 个txt文件...")
        for file_path in txt_files:
            try:
                if os.path.getsize(file_path) < args.min_bytes:
                    print(f"发现空文件或极小文件: {file_path}")
                    error_files.append(str(file_path))
                    continue
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    lines = file.readlines()
                    if len([l for l in lines if l.strip()]) < args.min_lines:
                        print(f"发现内容过少的文件: {file_path}")
                        error_files.append(str(file_path))
                        continue
                    for line in lines:
                        first_para = line.strip()
                        if first_para:
                            break
                    else:
                        first_para = ""
                if error_pattern.search(first_para):
                    print(f"发现包含错误提示的文件: {file_path}")
                    error_files.append(str(file_path))
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")
        print(f"检查完成。共发现 {len(error_files)} 个不合格文件。")
    else:
        check_and_delete_error_files(args.folder, min_bytes=args.min_bytes, min_lines=args.min_lines, min_chars=args.min_chars, max_line_length=args.max_line_length)

if __name__ == "__main__":
    # 直接指定要检查的文件夹路径
    folder_path = "/Volumes/ZimingYe/A_project/Mixed_data/Mix-data-0"
    check_and_delete_error_files(folder_path)