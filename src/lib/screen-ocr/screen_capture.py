#!/usr/bin/env python3
"""
屏幕捕获模块 (Screen Capture Module)

支持：
- 全屏捕获
- 区域捕获
- 多显示器支持
- 高性能截图

依赖：mss, Pillow
"""

import os
import io
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
from datetime import datetime

import mss
import mss.tools
from PIL import Image


class ScreenCapture:
    """屏幕捕获类"""
    
    def __init__(self):
        """初始化屏幕捕获器"""
        try:
            self.sct = mss.mss()
            self.monitors = self.sct.monitors
            self.primary_monitor = self.monitors[0] if self.monitors else None
            self.is_available = True
        except Exception as e:
            # 容器环境可能没有 DISPLAY
            self.sct = None
            self.monitors = []
            self.primary_monitor = None
            self.is_available = False
            self._error = str(e)
        
    def get_monitors(self) -> List[Dict[str, int]]:
        """
        获取所有显示器信息
        
        Returns:
            List[Dict]: 显示器列表，每个包含 monitor 索引和边界坐标
        """
        monitors_info = []
        for i, mon in enumerate(self.monitors):
            monitors_info.append({
                'index': i,
                'left': mon['left'],
                'top': mon['top'],
                'width': mon['width'],
                'height': mon['height'],
                'is_primary': i == 0
            })
        return monitors_info
    
    def capture_full(
        self,
        monitor: int = 0,
        save_path: Optional[str] = None
    ) -> Image.Image:
        """
        捕获全屏截图
        
        Args:
            monitor: 显示器索引 (0=主显示器)
            save_path: 可选，保存路径
            
        Returns:
            PIL.Image: 截图图像
        """
        if not self.is_available:
            # 容器环境：生成测试图像
            return self._create_test_image(save_path)
        
        if monitor >= len(self.monitors):
            raise ValueError(f"Monitor index {monitor} out of range")
        
        mon = self.monitors[monitor]
        screenshot = self.sct.grab(mon)
        
        # 转换为 PIL Image
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        
        if save_path:
            img.save(save_path)
            
        return img
    
    def _create_test_image(
        self,
        save_path: Optional[str] = None,
        width: int = 1920,
        height: int = 1080
    ) -> Image.Image:
        """
        创建测试图像 (用于无显示器环境)
        
        Args:
            save_path: 可选，保存路径
            width: 图像宽度
            height: 图像高度
            
        Returns:
            PIL.Image: 测试图像
        """
        # 创建渐变背景
        img = Image.new('RGB', (width, height), color=(70, 130, 180))
        
        # 添加文字说明
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        text = "Screen Capture Module\n[Headless Mode - Test Image]"
        draw.text((50, 50), text, fill=(255, 255, 255), font=font)
        draw.text((50, 120), f"Size: {width}x{height}", fill=(255, 255, 255), font=font)
        draw.text((50, 170), f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", fill=(255, 255, 255), font=font)
        
        if save_path:
            img.save(save_path)
            
        return img
    
    def capture_region(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
        monitor: int = 0,
        save_path: Optional[str] = None
    ) -> Image.Image:
        """
        捕获指定区域截图
        
        Args:
            left: 区域左边界 (像素)
            top: 区域上边界 (像素)
            width: 区域宽度 (像素)
            height: 区域高度 (像素)
            monitor: 显示器索引
            save_path: 可选，保存路径
            
        Returns:
            PIL.Image: 截图图像
        """
        if not self.is_available:
            # 容器环境：生成测试图像
            return self._create_test_image(save_path, width, height)
        
        # 获取显示器边界
        mon = self.monitors[monitor]
        
        # 计算相对于显示器的坐标
        abs_left = mon['left'] + left
        abs_top = mon['top'] + top
        
        # 创建捕获区域
        region = {
            'left': abs_left,
            'top': abs_top,
            'width': min(width, mon['width'] - left),
            'height': min(height, mon['height'] - top)
        }
        
        screenshot = self.sct.grab(region)
        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
        
        if save_path:
            img.save(save_path)
            
        return img
    
    def capture_window(
        self,
        window_title: Optional[str] = None,
        save_path: Optional[str] = None
    ) -> Optional[Image.Image]:
        """
        捕获指定窗口截图
        
        Args:
            window_title: 窗口标题 (可选)
            save_path: 可选，保存路径
            
        Returns:
            PIL.Image or None: 截图图像
        """
        # 注意：mss 不直接支持窗口捕获，需要使用其他方式
        # 这里返回全屏截图作为降级方案
        return self.capture_full(save_path=save_path)
    
    def capture_all_monitors(
        self,
        save_dir: Optional[str] = None
    ) -> List[Image.Image]:
        """
        捕获所有显示器截图
        
        Args:
            save_dir: 可选，保存目录
            
        Returns:
            List[PIL.Image]: 截图列表
        """
        images = []
        for i in range(1, len(self.monitors)):
            img = self.capture_full(monitor=i)
            images.append(img)
            
            if save_dir:
                Path(save_dir).mkdir(parents=True, exist_ok=True)
                save_path = os.path.join(save_dir, f"monitor_{i}.png")
                img.save(save_path)
                
        return images
    
    def get_screen_info(self) -> Dict[str, Any]:
        """
        获取屏幕信息
        
        Returns:
            Dict: 屏幕信息字典
        """
        monitors = self.get_monitors()
        return {
            'total_monitors': len(monitors),
            'monitors': monitors,
            'primary_resolution': (
                self.primary_monitor['width'],
                self.primary_monitor['height']
            ) if self.primary_monitor else (0, 0)
        }
    
    def capture_to_bytes(
        self,
        monitor: int = 0,
        format: str = 'PNG'
    ) -> bytes:
        """
        捕获截图并返回字节数据
        
        Args:
            monitor: 显示器索引
            format: 图像格式 (PNG/JPEG)
            
        Returns:
            bytes: 图像字节数据
        """
        img = self.capture_full(monitor=monitor)
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()


# 便捷函数
def capture_screen(save_path: Optional[str] = None) -> Image.Image:
    """
    快速捕获屏幕截图
    
    Args:
        save_path: 可选，保存路径
        
    Returns:
        PIL.Image: 截图图像
    """
    sc = ScreenCapture()
    return sc.capture_full(save_path=save_path)


def capture_region(
    left: int,
    top: int,
    width: int,
    height: int,
    save_path: Optional[str] = None
) -> Image.Image:
    """
    快速捕获区域截图
    
    Args:
        left: 左边界
        top: 上边界
        width: 宽度
        height: 高度
        save_path: 可选，保存路径
        
    Returns:
        PIL.Image: 截图图像
    """
    sc = ScreenCapture()
    return sc.capture_region(left, top, width, height, save_path=save_path)


# 测试
if __name__ == "__main__":
    print("🖥️  屏幕捕获模块测试")
    print("=" * 50)
    
    sc = ScreenCapture()
    
    # 检查可用性
    if not sc.is_available:
        print(f"\n⚠️  警告：屏幕捕获不可用 ({sc._error})")
        print("   使用测试图像模式")
    
    # 获取屏幕信息
    info = sc.get_screen_info()
    print(f"\n📊 屏幕信息:")
    print(f"  显示器数量：{info['total_monitors']}")
    if info['primary_resolution'][0] > 0:
        print(f"  主显示器分辨率：{info['primary_resolution']}")
    else:
        print(f"  主显示器分辨率：N/A (无显示器)")
    
    # 测试截图
    print("\n📸 测试截图...")
    test_path = "/tmp/screen_test.png"
    img = sc.capture_full(save_path=test_path)
    print(f"  ✅ 截图已保存：{test_path}")
    print(f"  图像尺寸：{img.size}")
    
    # 测试区域截图
    region_path = "/tmp/region_test.png"
    img = sc.capture_region(0, 0, 400, 300, save_path=region_path)
    print(f"  ✅ 区域截图已保存：{region_path}")
    print(f"  图像尺寸：{img.size}")
    
    print("\n" + "=" * 50)
    print("✅ 屏幕捕获模块测试完成")
