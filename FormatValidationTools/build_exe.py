"""
打包脚本 - 将应用打包成独立的可执行文件
支持 Windows (.exe) 和 macOS (.app)
运行: python build_exe.py
"""

import os
import sys
import subprocess
import shutil
import platform

# 配置控制台输出编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

def build():
    """打包应用"""
    
    current_os = platform.system()
    print("=" * 60)
    print("学位论文格式验证工具 - 打包程序")
    print(f"当前系统: {current_os}")
    print("=" * 60)
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print("✓ PyInstaller 安装完成")
    
    # 获取当前目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 根据操作系统设置路径分隔符（Windows用;，Mac/Linux用:）
    if current_os == 'Windows':
        separator = ';'
        app_name = '论文格式验证工具'
    else:
        separator = ':'
        app_name = 'ThesisValidator'  # Mac上避免中文名可能的问题
    
    # 构建PyInstaller命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        f'--name={app_name}',
        '--onefile',                    # 打包成单个文件
        '--windowed',                   # 不显示控制台窗口
        '--noconfirm',                  # 覆盖已有文件
        '--clean',                      # 清理临时文件
        f'--add-data=templates{separator}templates',           # 包含模板
        f'--add-data=validators{separator}validators',         # 包含验证器
        '--hidden-import=validators.run_all',
        '--hidden-import=validators.base_validator',
        '--hidden-import=validators.v01_page_setup',
        '--hidden-import=validators.v02_cover',
        '--hidden-import=validators.v03_abstract_cn',
        '--hidden-import=validators.v04_keywords_cn',
        '--hidden-import=validators.v05_abstract_en',
        '--hidden-import=validators.v06_keywords_en',
        '--hidden-import=validators.v07_toc',
        '--hidden-import=validators.v08_heading1',
        '--hidden-import=validators.v09_heading2',
        '--hidden-import=validators.v10_heading3',
        '--hidden-import=validators.v11_paragraph',
        '--hidden-import=validators.v12_word_count',
        '--hidden-import=validators.v13_figure',
        '--hidden-import=validators.v14_table',
        '--hidden-import=validators.v14b_table_continuation',
        '--hidden-import=validators.v15_three_line_table',
        '--hidden-import=validators.v16_formula',
        '--hidden-import=validators.v17_footnote',
        '--hidden-import=validators.v18_reference_title',
        '--hidden-import=validators.v19_reference_content',
        '--hidden-import=validators.v20_citation',
        '--hidden-import=validators.v21_punctuation',
        '--hidden-import=validators.v22_number',
        '--hidden-import=validators.v23_china_region',
        '--hidden-import=validators.v24_header',
        '--hidden-import=validators.v25_footer',
        '--hidden-import=validators.v26_appendix',
        '--hidden-import=validators.v27_acknowledgement',
        '--hidden-import=validators.v28_resume',
        '--hidden-import=validators.v29_spine',
        '--hidden-import=validators.v30_structure',
        'app.py'
    ]
    
    print("\n正在打包，请稍候（可能需要几分钟）...\n")
    
    # 执行打包
    result = subprocess.run(cmd, cwd=base_dir)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ 打包成功！")
        print("=" * 60)
        
        if current_os == 'Windows':
            exe_path = os.path.join(base_dir, 'dist', '论文格式验证工具.exe')
            if os.path.exists(exe_path):
                print(f"\n可执行文件位置:")
                print(f"  {exe_path}")
                print(f"\n文件大小: {os.path.getsize(exe_path) / 1024 / 1024:.1f} MB")
                print("\n使用方法:")
                print("  1. 双击运行 '论文格式验证工具.exe'")
                print("  2. 浏览器会自动打开")
                print("  3. 上传论文文档进行验证")
        else:
            # macOS
            app_path = os.path.join(base_dir, 'dist', 'ThesisValidator')
            if os.path.exists(app_path):
                print(f"\n可执行文件位置:")
                print(f"  {app_path}")
                print(f"\n文件大小: {os.path.getsize(app_path) / 1024 / 1024:.1f} MB")
                print("\n使用方法:")
                print("  1. 双击运行 'ThesisValidator'")
                print("  2. 浏览器会自动打开")
                print("  3. 上传论文文档进行验证")
                print("\n提示: 首次运行可能需要在系统设置中允许打开")
        
        print("\n你可以将 dist 文件夹中的文件发送给其他用户使用。")
    else:
        print("\n" + "=" * 60)
        print("✗ 打包失败，请检查错误信息")
        print("=" * 60)
    
    return result.returncode


if __name__ == '__main__':
    sys.exit(build())

