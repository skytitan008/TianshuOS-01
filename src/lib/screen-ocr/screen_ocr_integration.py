#!/usr/bin/env python3
"""
屏幕捕获 + OCR 集成模块

整合屏幕捕获和 OCR 识别功能，提供：
- 屏幕截图并识别文字
- 区域截图并识别
- 批量处理
- 性能测试
"""

import os
import time
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from screen_capture import ScreenCapture
from ocr_recognition import OCRRecognition


class ScreenOCR:
    """屏幕捕获 + OCR 集成类"""
    
    def __init__(
        self,
        ocr_lang: str = 'chi_sim+eng',
        ocr_oem: int = 3,
        ocr_psm: int = 3
    ):
        """
        初始化 ScreenOCR
        
        Args:
            ocr_lang: OCR 识别语言
            ocr_oem: OCR Engine Mode
            ocr_psm: Page Segmentation Mode
        """
        self.screen = ScreenCapture()
        self.ocr = OCRRecognition(lang=ocr_lang, oem=ocr_oem, psm=ocr_psm)
        
    def capture_and_recognize(
        self,
        monitor: int = 0,
        lang: Optional[str] = None,
        save_screenshot: bool = False,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        捕获屏幕并识别文字
        
        Args:
            monitor: 显示器索引
            lang: OCR 语言
            save_screenshot: 是否保存截图
            save_path: 保存路径
            
        Returns:
            Dict: 识别结果
        """
        start_time = time.time()
        
        # 捕获屏幕
        screenshot = self.screen.capture_full(monitor=monitor)
        
        # 保存截图
        if save_screenshot:
            if save_path is None:
                save_path = f"/tmp/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(save_path)
        
        # OCR 识别
        ocr_result = self.ocr.recognize(screenshot, lang=lang)
        
        # 添加性能信息
        processing_time = time.time() - start_time
        ocr_result['processing_time'] = processing_time
        ocr_result['screenshot_size'] = screenshot.size
        if save_screenshot:
            ocr_result['screenshot_path'] = save_path
        
        return ocr_result
    
    def capture_region_and_recognize(
        self,
        left: int,
        top: int,
        width: int,
        height: int,
        monitor: int = 0,
        lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        捕获屏幕区域并识别文字
        
        Args:
            left: 左边界
            top: 上边界
            width: 宽度
            height: 高度
            monitor: 显示器索引
            lang: OCR 语言
            
        Returns:
            Dict: 识别结果
        """
        start_time = time.time()
        
        # 捕获区域
        screenshot = self.screen.capture_region(left, top, width, height, monitor=monitor)
        
        # OCR 识别
        ocr_result = self.ocr.recognize(screenshot, lang=lang)
        
        # 添加性能信息
        processing_time = time.time() - start_time
        ocr_result['processing_time'] = processing_time
        ocr_result['region'] = {'left': left, 'top': top, 'width': width, 'height': height}
        
        return ocr_result
    
    def get_screen_info(self) -> Dict[str, Any]:
        """获取屏幕信息"""
        return self.screen.get_screen_info()
    
    def get_ocr_info(self) -> Dict[str, Any]:
        """获取 OCR 信息"""
        return {
            'available': self.ocr.is_available,
            'languages': self.ocr.get_available_languages(),
            'default_lang': self.ocr.lang
        }
    
    def run_performance_test(
        self,
        iterations: int = 5
    ) -> Dict[str, Any]:
        """
        运行性能测试
        
        Args:
            iterations: 测试次数
            
        Returns:
            Dict: 性能测试结果
        """
        print(f"🚀 开始性能测试 ({iterations} 次迭代)...")
        
        times = []
        results = []
        
        for i in range(iterations):
            result = self.capture_and_recognize(monitor=0)
            times.append(result.get('processing_time', 0))
            results.append(result)
            
            print(f"  迭代 {i+1}/{iterations}: {result.get('processing_time', 0)*1000:.1f}ms")
        
        # 计算统计
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        return {
            'iterations': iterations,
            'avg_processing_time_ms': avg_time * 1000,
            'min_processing_time_ms': min_time * 1000,
            'max_processing_time_ms': max_time * 1000,
            'avg_text_length': sum(len(r.get('text', '')) for r in results) / len(results),
            'avg_confidence': sum(r.get('confidence', 0) for r in results) / len(results),
            'results': results
        }


# 测试
if __name__ == "__main__":
    print("🖥️📝 ScreenOCR 集成模块测试")
    print("=" * 60)
    
    # 创建实例
    screen_ocr = ScreenOCR(ocr_lang='chi_sim+eng')
    
    # 获取信息
    print("\n📊 系统信息:")
    screen_info = screen_ocr.get_screen_info()
    print(f"  屏幕捕获：{'可用' if screen_info.get('total_monitors', 0) > 0 else '不可用 (容器环境)'}")
    
    ocr_info = screen_ocr.get_ocr_info()
    print(f"  OCR 引擎：{'可用' if ocr_info['available'] else '不可用'}")
    print(f"  支持语言：{', '.join(ocr_info['languages'])}")
    
    # 性能测试
    print("\n⏱️  性能测试:")
    perf = screen_ocr.run_performance_test(iterations=3)
    
    print(f"\n📈 性能统计:")
    print(f"  平均处理时间：{perf['avg_processing_time_ms']:.1f}ms")
    print(f"  最小处理时间：{perf['min_processing_time_ms']:.1f}ms")
    print(f"  最大处理时间：{perf['max_processing_time_ms']:.1f}ms")
    print(f"  平均置信度：{perf['avg_confidence']:.1f}%")
    print(f"  平均文本长度：{perf['avg_text_length']:.1f} 字符")
    
    # 保存测试报告
    report_path = "/root/tasks/task-20260409-144100-screen-ocr/output/ocr-test-report.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# OCR 性能测试报告\n\n")
        f.write(f"**测试日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**测试次数**: {perf['iterations']}\n\n")
        f.write("## 性能指标\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 平均处理时间 | {perf['avg_processing_time_ms']:.1f}ms |\n")
        f.write(f"| 最小处理时间 | {perf['min_processing_time_ms']:.1f}ms |\n")
        f.write(f"| 最大处理时间 | {perf['max_processing_time_ms']:.1f}ms |\n")
        f.write(f"| 平均置信度 | {perf['avg_confidence']:.1f}% |\n")
        f.write(f"| 平均文本长度 | {perf['avg_text_length']:.1f} 字符 |\n\n")
        f.write("## 测试环境\n\n")
        f.write(f"- OCR 引擎：Tesseract {ocr_info['languages']}\n")
        f.write(f"- 语言包：chi_sim, eng\n")
        f.write(f"- 屏幕模式：{'Headless (容器)' if screen_info.get('total_monitors', 0) == 0 else '正常'}\n")
    
    print(f"\n✅ 测试报告已保存：{report_path}")
    
    print("\n" + "=" * 60)
    print("✅ ScreenOCR 集成模块测试完成")
