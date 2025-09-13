#!/usr/bin/env python3
"""
文件夹文档翻译工具 - 将文件夹中的文档翻译成英文

用法:
    python translator.py <输入文件夹> <输出文件夹> [--recursive]

参数:
    <输入文件夹>  包含要翻译文档的文件夹路径
    <输出文件夹>  翻译后文档的保存文件夹路径
    --recursive   递归处理子文件夹中的文件
"""

import os
import sys
import argparse
from pathlib import Path
import logging
from tqdm import tqdm
from googletrans import Translator
from langdetect import detect
import time
import requests
import hashlib
import random
import uuid

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('translation.log')
    ]
)
logger = logging.getLogger(__name__)

# 支持的文件类型
SUPPORTED_EXTENSIONS = {'.txt', '.md', '.rst', '.log'}

def setup_translator():
    """初始化翻译器"""
    return Translator()

def youdao_translate(text, appKey, appSecret, from_lang='auto', to_lang='en'):
    if not text.strip():
        return text
    endpoint = "https://openapi.youdao.com/api"
    salt = str(uuid.uuid4())
    curtime = str(int(time.time()))
    sign_str = appKey + truncate(text) + salt + curtime + appSecret
    sign = hashlib.sha256(sign_str.encode()).hexdigest()
    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appKey': appKey,
        'salt': salt,
        'sign': sign,
        'signType': 'v3',
        'curtime': curtime
    }
    try:
        resp = requests.post(endpoint, data=params, timeout=10)
        result = resp.json()
        if 'translation' in result:
            return ''.join(result['translation'])
        else:
            logger.error(f"有道翻译API返回异常: {result}")
            return text
    except Exception as e:
        logger.error(f"有道翻译API请求失败: {e}")
        return text

def truncate(q):
    if q is None:
        return None
    size = len(q)
    return q if size <= 20 else q[:10] + str(size) + q[-10:]

def translate_text(translator, text, retries=3, delay=1):
    """只要不是英文就翻译成英文，英文内容直接返回"""
    try:
        if not text.strip():
            return text
        lang = 'en'
        try:
            lang = detect(text)
        except Exception:
            pass
        if lang != 'en':
            return translator.translate(text, src=lang, dest='en').text
        else:
            return text  # 英文直接返回
    except Exception as e:
        logger.error(f"翻译失败: {e}")
        return text

def get_files_to_translate(input_folder, recursive=False):
    """获取需要翻译的文件列表"""
    input_path = Path(input_folder)
    files_to_translate = []
    
    try:
        if recursive:
            # 递归获取所有文件
            for file_path in input_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files_to_translate.append(file_path)
        else:
            # 只获取当前文件夹中的文件
            for file_path in input_path.glob('*'):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    files_to_translate.append(file_path)
    except Exception as e:
        logger.error(f"获取文件列表时出错: {e}")
        return []
    
    return files_to_translate

def is_english(text):
    """检测文本是否为英文"""
    try:
        lang = detect(text)
        return lang == 'en'
    except Exception:
        return False

def translate_file(translator, input_file, input_folder, output_folder, failed_folder):
    """翻译单个文件，英文原文和翻译结果都输出，翻译失败的放到failed_folder"""
    try:
        # 读取源文件
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            logger.error(f"无法解码文件 {input_file}: {e}")
            return False
        # 计算相对路径，保持目录结构
        rel_path = input_file.relative_to(input_folder)
        output_path = Path(output_folder) / rel_path.parent / f"En_{input_file.name}"
        failed_path = Path(failed_folder) / rel_path.parent / f"Failed_{input_file.name}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        failed_path.parent.mkdir(parents=True, exist_ok=True)
        # 跳过已为英文的文件，直接复制到输出
        if is_english(content):
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"英文文件直接复制: {input_file} -> {output_path}")
            return True
        # 翻译内容
        translated_content = translate_text(translator, content)
        # 检查翻译是否失败（内容未变或为空）
        if not translated_content.strip() or translated_content.strip() == content.strip():
            with open(failed_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.warning(f"翻译失败，已保存原文: {input_file} -> {failed_path}")
            return False
        # 写入翻译后的内容
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        logger.info(f"已翻译: {input_file} -> {output_path}")
        return True
    except Exception as e:
        logger.error(f"处理文件 {input_file} 时出错: {e}")
        # 保存到失败目录
        try:
            with open(failed_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception:
            pass
        return False

def baidu_translate(text, appid, secretKey, from_lang='auto', to_lang='en'):
    if not text.strip():
        return text
    endpoint = "https://fanyi-api.baidu.com/api/trans/vip/translate"
    salt = str(random.randint(32768, 65536))
    sign = appid + text + salt + secretKey
    sign = hashlib.md5(sign.encode()).hexdigest()
    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appid': appid,
        'salt': salt,
        'sign': sign
    }
    try:
        resp = requests.get(endpoint, params=params, timeout=10)
        result = resp.json()
        if 'trans_result' in result:
            return ''.join([item['dst'] for item in result['trans_result']])
        else:
            logger.error(f"百度翻译API返回异常: {result}")
            return text
    except Exception as e:
        logger.error(f"百度翻译API请求失败: {e}")
        return text

def main():
    input_folder = "/Volumes/ZimingYe/A_project/Mixed_data/Mix-data-0"
    output_folder = "/Volumes/ZimingYe/A_project/Mixed_data/Mix-data-Translation"
    failed_folder = "/Volumes/ZimingYe/A_project/Mixed_data/Mix-data-0-other"
    recursive = True  # 如需递归子文件夹，设为True，否则False

    # 检查输入文件夹是否存在
    if not os.path.isdir(input_folder):
        logger.error(f"错误: {input_folder} 不是一个有效的文件夹")
        return 1

    # 创建输出文件夹
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    # 创建失败文件夹
    failed_path = Path(failed_folder)
    failed_path.mkdir(parents=True, exist_ok=True)

    # 初始化翻译器
    translator = Translator()

    # 获取需要翻译的文件列表
    files_to_translate = get_files_to_translate(input_folder, recursive)

    if not files_to_translate:
        logger.warning(f"在 {input_folder} 中没有找到支持的文件类型")
        return 0

    # 显示支持的文件类型
    logger.info(f"支持的文件类型: {', '.join(SUPPORTED_EXTENSIONS)}")
    logger.info(f"找到 {len(files_to_translate)} 个文件需要翻译")

    # 翻译文件
    success_count = 0
    with tqdm(total=len(files_to_translate), desc="翻译进度") as pbar:
        for file_path in files_to_translate:
            if file_path.name.startswith("._"):
                continue
            if translate_file(translator, file_path, input_folder, output_folder, failed_folder):
                success_count += 1
            pbar.update(1)

    # 输出统计信息
    logger.info(f"翻译完成: 成功 {success_count}/{len(files_to_translate)} 个文件")
    logger.info(f"翻译后的文件保存在: {output_folder}")
    logger.info(f"翻译失败的文件保存在: {failed_folder}")

    return 0

if __name__ == "__main__":
    sys.exit(main())