# gpu_test.py
import torch
import sys

def basic_gpu_test():
    print("=" * 60)
    print("🔍 基础GPU测试")
    print("=" * 60)
    
    # 1. 检查Python和PyTorch版本
    print(f"Python 版本: {sys.version}")
    print(f"PyTorch 版本: {torch.__version__}")
    
    # 2. 检查CUDA是否可用
    cuda_available = torch.cuda.is_available()
    print(f"CUDA 是否可用: {cuda_available}")
    
    if not cuda_available:
        print("\n❌ CUDA不可用！可能的原因：")
        print("1. 没有NVIDIA显卡")
        print("2. 没有安装NVIDIA驱动")
        print("3. 安装的是CPU版本的PyTorch")
        print("4. CUDA工具包没有安装或版本不匹配")
        return False
    
    # 3. 检查GPU信息
    print(f"\n✅ GPU 数量: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"   显存: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
    
    # 4. 简单的GPU计算测试
    print("\n🧪 运行GPU计算测试...")
    try:
        # 在GPU上创建张量
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        
        # 进行矩阵乘法
        z = torch.mm(x, y)
        
        print("✅ GPU计算测试通过！")
        print(f"   结果张量设备: {z.device}")
        print(f"   结果形状: {z.shape}")
        
        return True
    except Exception as e:
        print(f"❌ GPU计算测试失败: {e}")
        return False

if __name__ == "__main__":
    basic_gpu_test()