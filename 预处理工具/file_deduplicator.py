#!/usr/bin/env python3
"""
文件去重工具 - 比较文件夹中的所有文件，删除内容相同的重复文件

用法:
    python file_deduplicator.py <文件夹路径> [--dry-run] [--recursive]

参数:
    <文件夹路径>  要去重的文件夹路径
    --dry-run     仅显示将要删除的文件，不实际删除
    --recursive   递归处理子文件夹
"""

import os
import sys
import hashlib
import argparse
import traceback
from pathlib import Path
from collections import defaultdict
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('file_deduplication.log')
    ]
)
logger = logging.getLogger(__name__)

def calculate_file_hash(file_path, chunk_size=8192):
    """计算文件的MD5哈希值"""
    try:
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希值时出错 {file_path}: {e}")
        return None

def get_files_by_size(folder_path, recursive=False):
    """按大小对文件进行分组"""
    files_by_size = defaultdict(list)
    folder = Path(folder_path)
    
    try:
        if recursive:
            # 递归处理所有子文件夹
            for file_path in folder.glob('**/*.txt'):
                if file_path.is_file():
                    try:
                        # 获取文件大小
                        file_size = file_path.stat().st_size
                        files_by_size[file_size].append(str(file_path))
                    except Exception as e:
                        logger.error(f"获取文件大小时出错 {file_path}: {e}")
        else:
            # 只处理指定文件夹中的文件
            for file_path in folder.glob('*.txt'):
                if file_path.is_file():
                    try:
                        file_size = file_path.stat().st_size
                        files_by_size[file_size].append(str(file_path))
                    except Exception as e:
                        logger.error(f"获取文件大小时出错 {file_path}: {e}")
    except Exception as e:
        logger.error(f"访问文件夹时出错 {folder}: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
    
    return files_by_size

def find_duplicate_files(folder_path, recursive=False):
    """查找重复文件"""
    logger.info(f"开始在 {folder_path} 中查找重复文件...")
    
    # 第一步：按文件大小分组
    files_by_size = get_files_by_size(folder_path, recursive)
    logger.info(f"找到 {sum(len(files) for files in files_by_size.values())} 个文件，分为 {len(files_by_size)} 个不同的大小组")
    
    # 过滤出可能的重复文件（大小相同的文件）
    potential_duplicates = {size: files for size, files in files_by_size.items() if len(files) > 1}
    logger.info(f"找到 {len(potential_duplicates)} 个可能包含重复文件的大小组")
    
    if not potential_duplicates:
        logger.info("没有找到可能的重复文件")
        return []
    
    # 第二步：计算文件哈希值
    duplicates = []
    total_files = sum(len(files) for files in potential_duplicates.values())
    
    with tqdm(total=total_files, desc="计算文件哈希值") as pbar:
        for size, files in potential_duplicates.items():
            # 跳过空文件
            if size == 0:
                logger.info(f"跳过 {len(files)} 个空文件")
                continue
            
            # 使用哈希值对文件进行分组
            files_by_hash = defaultdict(list)
            
            # 使用线程池并行计算哈希值
            with ThreadPoolExecutor(max_workers=8) as executor:
                hash_results = list(executor.map(calculate_file_hash, files))
                
                for file_path, file_hash in zip(files, hash_results):
                    pbar.update(1)
                    if file_hash:
                        files_by_hash[file_hash].append(file_path)
            
            # 找出哈希值相同的文件组（重复文件）
            for file_hash, file_paths in files_by_hash.items():
                if len(file_paths) > 1:
                    # 保留第一个文件，其余的视为重复
                    original = file_paths[0]
                    duplicates_in_group = file_paths[1:]
                    duplicates.append((original, duplicates_in_group))
    
    return duplicates

def delete_duplicate_files(duplicates, dry_run=False):
    """删除重复文件"""
    if not duplicates:
        logger.info("没有重复文件需要删除")
        return 0
    
    total_deleted = 0
    total_size_saved = 0
    
    for original, duplicate_files in duplicates:
        original_size = os.path.getsize(original)
        
        for duplicate in duplicate_files:
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] 将删除: {duplicate} (保留: {original})")
                else:
                    os.remove(duplicate)
                    logger.info(f"已删除: {duplicate} (保留: {original})")
                
                total_deleted += 1
                total_size_saved += original_size
            except Exception as e:
                logger.error(f"删除文件时出错 {duplicate}: {e}")
    
    # 转换为更易读的大小格式
    size_saved_mb = total_size_saved / (1024 * 1024)
    
    if dry_run:
        logger.info(f"[DRY RUN] 将删除 {total_deleted} 个重复文件，节省 {size_saved_mb:.2f} MB 空间")
    else:
        logger.info(f"已删除 {total_deleted} 个重复文件，节省 {size_saved_mb:.2f} MB 空间")
    
    return total_deleted

def generate_report(duplicates, output_file="deduplication_report.txt"):
    """生成去重报告"""
    if not duplicates:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("没有找到重复文件\n")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("文件去重报告\n")
        f.write("=" * 80 + "\n\n")
        
        total_groups = len(duplicates)
        total_duplicates = sum(len(dupes) for _, dupes in duplicates)
        total_size_saved = sum(os.path.getsize(original) * len(dupes) for original, dupes in duplicates)
        
        f.write(f"重复文件组数量: {total_groups}\n")
        f.write(f"重复文件总数: {total_duplicates}\n")
        f.write(f"节省空间: {total_size_saved / (1024 * 1024):.2f} MB\n\n")
        
        for i, (original, dupes) in enumerate(duplicates, 1):
            f.write(f"组 {i}:\n")
            f.write(f"  保留: {original}\n")
            f.write(f"  删除: {len(dupes)} 个文件\n")
            for dupe in dupes:
                f.write(f"    - {dupe}\n")
            f.write("\n")

def main():
    # 直接指定路径，不用命令行
    class Args:
        folder_path = "/Volumes/ZimingYe/A_project/Mixed_data/Mix-data-0"
        dry_run = False
        recursive = True
        report = "deduplication_report.txt"
    args = Args()
    
    folder_path = Path(args.folder_path).resolve()
    
    logger.info(f"开始处理文件夹: {folder_path}")
    
    if not folder_path.is_dir():
        logger.error(f"错误: {folder_path} 不是一个有效的文件夹")
        return 1
    
    # 检查文件夹是否可访问
    try:
        next(folder_path.iterdir(), None)
    except PermissionError:
        logger.error(f"错误: 没有权限访问文件夹 {folder_path}")
        return 1
    except Exception as e:
        logger.error(f"访问文件夹时出错 {folder_path}: {e}")
        return 1
    
    try:
        # 查找重复文件
        logger.info(f"开始查找重复文件...")
        duplicates = find_duplicate_files(str(folder_path), args.recursive)
        
        # 生成报告
        logger.info(f"生成去重报告...")
        generate_report(duplicates, args.report)
        
        # 删除重复文件
        logger.info(f"{'[DRY RUN] 模拟' if args.dry_run else '开始'}删除重复文件...")
        delete_duplicate_files(duplicates, args.dry_run)
        
        logger.info(f"去重完成，详细报告已保存到 {args.report}")
        return 0
    
    except Exception as e:
        logger.error(f"程序执行过程中出错: {e}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())