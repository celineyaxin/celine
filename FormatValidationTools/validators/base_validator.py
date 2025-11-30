"""
验证器基类
所有验证器都继承此基类，提供统一的接口和报告格式
"""

import sys
import os
from abc import ABC, abstractmethod
from docx import Document

# 配置控制台输出编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass


class BaseValidator(ABC):
    """验证器基类"""
    
    # 子类必须定义的属性
    name: str = "基类验证器"
    description: str = "验证器描述"
    standard_ref: str = "规范引用"
    
    def __init__(self, doc_path: str, thesis_type: str = '博士'):
        """
        初始化验证器
        
        Args:
            doc_path: Word文档路径
            thesis_type: 论文类型（本科/硕士/博士）
        """
        self.doc_path = doc_path
        self.doc = Document(doc_path)
        self.thesis_type = thesis_type
        
        # 验证结果列表
        self.errors = []    # 错误（必须修复）
        self.warnings = []  # 警告（建议修复）
        self.info = []      # 信息（通过项）
    
    @abstractmethod
    def validate(self) -> bool:
        """
        执行验证
        
        Returns:
            bool: 是否通过验证（无错误）
        """
        pass
    
    def add_error(self, message: str):
        """添加错误"""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """添加警告"""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """添加信息"""
        self.info.append(message)
    
    def clear_results(self):
        """清除验证结果"""
        self.errors = []
        self.warnings = []
        self.info = []
    
    def get_report(self) -> dict:
        """
        获取验证报告
        
        Returns:
            dict: 包含验证结果的字典
        """
        return {
            'validator': self.name,
            'description': self.description,
            'standard_ref': self.standard_ref,
            'thesis_type': self.thesis_type,
            'passed': len(self.errors) == 0,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'info': self.info.copy(),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
        }
    
    def print_report(self):
        """打印验证报告"""
        print()
        print("=" * 70)
        print(f"{self.name} ({self.standard_ref})")
        print("=" * 70)
        print()
        
        # 打印信息
        if self.info:
            print("[信息]")
            for item in self.info:
                print(f"  ✓ {item}")
            print()
        
        # 打印警告
        if self.warnings:
            print(f"[警告] {len(self.warnings)} 项")
            for item in self.warnings[:10]:
                print(f"  ! {item}")
            if len(self.warnings) > 10:
                print(f"  ... 还有 {len(self.warnings) - 10} 条警告")
            print()
        
        # 打印错误
        if self.errors:
            print(f"[错误] {len(self.errors)} 项 (必须修复)")
            for item in self.errors[:10]:
                print(f"  ✗ {item}")
            if len(self.errors) > 10:
                print(f"  ... 还有 {len(self.errors) - 10} 条错误")
            print()
        
        # 打印结论
        print("-" * 70)
        if not self.errors and not self.warnings:
            print("✓ 验证结果: 通过")
        elif not self.errors:
            print(f"○ 验证结果: 基本通过（有 {len(self.warnings)} 条警告）")
        else:
            print(f"✗ 验证结果: 未通过（有 {len(self.errors)} 条错误）")
        print("=" * 70)
        
        return len(self.errors) == 0
    
    def run(self) -> bool:
        """
        运行验证并打印报告
        
        Returns:
            bool: 是否通过验证
        """
        self.clear_results()
        self.validate()
        return self.print_report()


def run_validator(validator_class, doc_path: str, thesis_type: str = '博士'):
    """
    运行指定的验证器
    
    Args:
        validator_class: 验证器类
        doc_path: 文档路径
        thesis_type: 论文类型
    """
    if not os.path.exists(doc_path):
        print(f"错误: 文件不存在 - {doc_path}")
        return False
    
    validator = validator_class(doc_path, thesis_type)
    return validator.run()


def parse_args():
    """解析命令行参数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='论文格式验证器')
    parser.add_argument('doc_path', help='Word文档路径')
    parser.add_argument('--type', dest='thesis_type', default='博士',
                        choices=['本科', '硕士', '博士', 'bachelor', 'master', 'phd'],
                        help='论文类型（默认：博士）')
    
    args = parser.parse_args()
    
    # 转换英文类型名
    type_mapping = {
        'bachelor': '本科',
        'master': '硕士',
        'phd': '博士',
    }
    args.thesis_type = type_mapping.get(args.thesis_type, args.thesis_type)
    
    return args

