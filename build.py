#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的APK构建脚本

此脚本提供了一个清晰、模块化的方式来构建Android APK，
包含环境检查、依赖管理、配置参数化和详细的错误处理。
"""

import os
import sys
import subprocess
import json
import argparse
import logging
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("build.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 默认配置
DEFAULT_CONFIG = {
    "app_name": "SalaryCalculator",
    "package_name": "org.test.salarycalculator",
    "package_domain": "org.test",
    "version": "1.0",
    "requirements": [
        "kivy==2.3.0",
        "certifi==2023.7.22",
        "pyjnius==1.6.1",
        "openpyxl==3.1.2",
        "pandas==2.0.3",
        "matplotlib==3.7.2",
        "reportlab==3.6.12",
        "requests==2.31.0",
        "numpy==1.24.4"
    ],
    "orientation": "portrait",
    "screen": "fullscreen",
    "android_api": 28,
    "ndk_version": "21.4.7075529",
    "sdk_version": 28,
    "archs": ["armeabi-v7a"],
    "source_dir": ".",  # 根目录，通过符号链接访问main.py
    "output_dir": "./output",
    "android_sdk_path": "./android-sdk",
    "java_home": "/usr/lib/jvm/java-11-openjdk-amd64",
    "main_py": "main.py"
}

def check_environment(config):
    """检查构建环境"""
    logger.info("===== 检查构建环境 =====")
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        logger.error("需要Python 3.7或更高版本")
        return False
    
    logger.info(f"Python版本: {sys.version}")
    
    # 检查Java环境
    java_home = os.environ.get('JAVA_HOME', config['java_home'])
    if not os.path.exists(java_home):
        logger.error(f"JAVA_HOME路径不存在: {java_home}")
        return False
    
    # 检查Android SDK
    sdk_path = os.environ.get('ANDROID_HOME', config['android_sdk_path'])
    if not os.path.exists(sdk_path):
        logger.error(f"Android SDK路径不存在: {sdk_path}")
        return False
    
    # 检查main.py是否存在
    main_py = PROJECT_ROOT / config['main_py']
    if not main_py.exists():
        logger.error(f"主入口文件不存在: {main_py}")
        return False
    
    # 确保输出目录存在
    output_dir = PROJECT_ROOT / config['output_dir']
    output_dir.mkdir(exist_ok=True)
    
    logger.info("环境检查通过")
    return True

def install_python_dependencies(config):
    """安装Python依赖"""
    logger.info("===== 安装Python依赖 =====")
    
    # 首先安装构建依赖
    build_deps = [
        "buildozer==1.5.0",
        "python-for-android==2024.1.21",
        "importlib-metadata==4.8.3",
        "Cython==0.29.33"
    ]
    
    try:
        # 安装构建依赖
        for dep in build_deps:
            logger.info(f"安装构建依赖: {dep}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        
        # 从requirements.txt安装所有依赖
        if os.path.exists("requirements.txt"):
            logger.info("从requirements.txt安装应用依赖")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        logger.info("Python依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"安装Python依赖失败: {e}")
        return False

def setup_environment_variables(config):
    """设置环境变量"""
    logger.info("===== 设置环境变量 =====")
    
    # 设置环境变量
    os.environ['JAVA_HOME'] = config['java_home']
    os.environ['ANDROID_HOME'] = config['android_sdk_path']
    os.environ['PATH'] += f":{config['android_sdk_path']}/tools"
    os.environ['PATH'] += f":{config['android_sdk_path']}/platform-tools"
    
    logger.info(f"JAVA_HOME: {os.environ['JAVA_HOME']}")
    logger.info(f"ANDROID_HOME: {os.environ['ANDROID_HOME']}")
    
    return True

def build_apk(config):
    """使用python-for-android构建APK"""
    logger.info("===== 开始构建APK =====")
    
    # 构建p4a命令
    cmd = [
        "p4a", "apk",
        "--name", config['app_name'],
        "--package", config['package_name'],
        "--version", config['version'],
        "--orientation", config['orientation'],
        "--window", config['screen'],
        "--private", str(PROJECT_ROOT / config['source_dir']),
        "--output-dir", str(PROJECT_ROOT / config['output_dir']),
        "--arch", ",".join(config['archs']),
        "--sdk-dir", config['android_sdk_path'],
        "--ndk-dir", "./android-ndk",
        "--ndk-api", str(config['android_api']),
        "--sdk-version", str(config['sdk_version']),
        "--log-level", "2",
        "--requirements", ",".join(config['requirements'])
    ]
    
    logger.info(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 执行构建命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # 实时输出构建日志
        with open("build_detail.log", "w") as log_file:
            for line in process.stdout:
                print(line.strip())
                log_file.write(line)
                log_file.flush()
        
        process.wait()
        
        # 计算构建时间
        build_time = time.time() - start_time
        logger.info(f"构建完成，耗时: {build_time:.2f} 秒")
        
        if process.returncode == 0:
            logger.info("APK构建成功")
            return True
        else:
            logger.error(f"APK构建失败，返回码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"构建过程中发生错误: {e}")
        return False

def verify_build_result(config):
    """验证构建结果"""
    logger.info("===== 验证构建结果 =====")
    
    output_dir = PROJECT_ROOT / config['output_dir']
    
    # 查找APK文件
    apk_files = list(output_dir.glob("*.apk"))
    
    if apk_files:
        for apk_file in apk_files:
            logger.info(f"找到APK文件: {apk_file}")
            logger.info(f"文件大小: {apk_file.stat().st_size / (1024 * 1024):.2f} MB")
        return True
    else:
        logger.error("未找到生成的APK文件")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='构建Android APK')
    parser.add_argument('--config', help='配置文件路径', default=None)
    parser.add_argument('--clean', action='store_true', help='清理构建缓存')
    args = parser.parse_args()
    
    # 加载配置
    config = DEFAULT_CONFIG.copy()
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
            logger.info(f"已加载用户配置: {args.config}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return 1
    
    # 清理构建缓存
    if args.clean:
        logger.info("清理构建缓存...")
        cache_dirs = [".buildozer", "./.buildozer"]
        for cache_dir in cache_dirs:
            path = PROJECT_ROOT / cache_dir
            if path.exists():
                try:
                    import shutil
                    shutil.rmtree(path)
                    logger.info(f"已删除缓存目录: {path}")
                except Exception as e:
                    logger.error(f"删除缓存目录失败 {path}: {e}")
    
    # 执行构建流程
    steps = [
        ("环境检查", check_environment),
        ("安装Python依赖", install_python_dependencies),
        ("设置环境变量", setup_environment_variables),
        ("构建APK", build_apk),
        ("验证构建结果", verify_build_result)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"执行: {step_name}")
        if not step_func(config):
            logger.error(f"步骤失败: {step_name}")
            return 1
        logger.info(f"步骤完成: {step_name}")
    
    logger.info("构建流程全部完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main())