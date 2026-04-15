#!/usr/bin/env python3
"""
OCR 文字识别模块 (OCR Recognition Module)

支持：
- 中英文文字识别
- 图像文件识别
- 字节数据识别
- 识别结果置信度

依赖：pytesseract, Pillow, Tesseract OCR
"""

import os
import io
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import pytesseract
from PIL import Image


class OCRRecognition:
    """OCR 文字识别类"""
    
    def __init__(
        self,
        lang: str = 'chi_sim+eng',
        oem: int = 3,
        psm: int = 3
    ):
        """
        初始化 OCR 识别器
        
        Args:
            lang: 识别语言 (chi_sim=简体中文，eng=英文)
            oem: OCR Engine Mode (3=默认，基于 LSTM)
            psm: Page Segmentation Mode (3=自动，4=单列，6=单行)
        """
        self.lang = lang
        self.oem = oem
        self.psm = psm
        self.is_available = self._check_tesseract()
        
    def _check_tesseract(self) -> bool:
        """检查 Tesseract 是否可用"""
        try:
            version = pytesseract.get_tesseract_version()
            print(f"✅ Tesseract version: {version}")
            return True
        except Exception as e:
            print(f"⚠️  Tesseract 不可用：{e}")
            return False
    
    def recognize(
        self,
        image: Union[str, Image.Image, bytes],
        lang: Optional[str] = None,
        return_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        识别图像中的文字
        
        Args:
            image: 图像路径、PIL Image 或字节数据
            lang: 识别语言 (可选，覆盖默认值)
            return_confidence: 是否返回置信度
            
        Returns:
            Dict: 识别结果
                - text: 识别的文本
                - confidence: 平均置信度 (0-100)
                - words: 单词级识别结果 (可选)
        """
        if not self.is_available:
            return {
                'success': False,
                'text': '',
                'confidence': 0,
                'error': 'Tesseract OCR not available'
            }
        
        try:
            # 加载图像
            img = self._load_image(image)
            
            # 配置识别参数
            config = f'--oem {self.oem} --psm {self.psm}'
            ocr_lang = lang or self.lang
            
            # 执行识别
            text = pytesseract.image_to_string(img, lang=ocr_lang, config=config)
            
            result = {
                'success': True,
                'text': text.strip(),
                'confidence': 0,
                'language': ocr_lang
            }
            
            # 获取置信度
            if return_confidence:
                data = pytesseract.image_to_data(
                    img,
                    lang=ocr_lang,
                    config=config,
                    output_type=pytesseract.Output.DICT
                )
                
                # 计算平均置信度
                confidences = [c for c in data['conf'] if c > 0]
                if confidences:
                    result['confidence'] = sum(confidences) / len(confidences)
                
                # 添加单词级结果
                result['words'] = self._extract_words(data)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'confidence': 0,
                'error': str(e)
            }
    
    def recognize_region(
        self,
        image: Union[str, Image.Image, bytes],
        left: int,
        top: int,
        width: int,
        height: int,
        lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        识别图像指定区域的文字
        
        Args:
            image: 图像路径、PIL Image 或字节数据
            left: 区域左边界
            top: 区域上边界
            width: 区域宽度
            height: 区域高度
            lang: 识别语言
            
        Returns:
            Dict: 识别结果
        """
        img = self._load_image(image)
        
        # 裁剪区域
        region_img = img.crop((left, top, left + width, top + height))
        
        return self.recognize(region_img, lang=lang)
    
    def recognize_from_file(
        self,
        file_path: str,
        lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从文件识别文字
        
        Args:
            file_path: 图像文件路径
            lang: 识别语言
            
        Returns:
            Dict: 识别结果
        """
        return self.recognize(file_path, lang=lang)
    
    def recognize_from_bytes(
        self,
        image_bytes: bytes,
        lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从字节数据识别文字
        
        Args:
            image_bytes: 图像字节数据
            lang: 识别语言
            
        Returns:
            Dict: 识别结果
        """
        return self.recognize(image_bytes, lang=lang)
    
    def get_available_languages(self) -> List[str]:
        """
        获取可用的语言包
        
        Returns:
            List[str]: 语言列表
        """
        try:
            langs = pytesseract.get_languages(config='')
            return langs
        except:
            return []
    
    def _load_image(self, image: Union[str, Image.Image, bytes]) -> Image.Image:
        """
        加载图像
        
        Args:
            image: 图像路径、PIL Image 或字节数据
            
        Returns:
            PIL.Image: 图像对象
        """
        if isinstance(image, Image.Image):
            return image
        elif isinstance(image, bytes):
            return Image.open(io.BytesIO(image))
        elif isinstance(image, str):
            return Image.open(image)
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
    
    def _extract_words(self, data: Dict) -> List[Dict[str, Any]]:
        """
        提取单词级识别结果
        
        Args:
            data: image_to_data 返回的数据
            
        Returns:
            List[Dict]: 单词列表
        """
        words = []
        n_boxes = len(data['level'])
        
        for i in range(n_boxes):
            if data['text'][i].strip():
                words.append({
                    'text': data['text'][i],
                    'confidence': data['conf'][i],
                    'bbox': {
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    }
                })
        
        return words


# 便捷函数
def recognize_text(
    image_path: str,
    lang: str = 'chi_sim+eng'
) -> str:
    """
    快速识别图像文字
    
    Args:
        image_path: 图像文件路径
        lang: 识别语言
        
    Returns:
        str: 识别的文本
    """
    ocr = OCRRecognition(lang=lang)
    result = ocr.recognize(image_path)
    return result.get('text', '')


# 测试
if __name__ == "__main__":
    print("📝 OCR 文字识别模块测试")
    print("=" * 50)
    
    ocr = OCRRecognition(lang='chi_sim+eng')
    
    # 检查可用性
    if not ocr.is_available:
        print("\n⚠️  Tesseract OCR 不可用")
        print("   请安装：apt-get install tesseract-ocr tesseract-ocr-chi-sim")
    else:
        # 获取可用语言
        langs = ocr.get_available_languages()
        print(f"\n📚 可用语言包：{', '.join(langs)}")
        
        # 测试识别
        test_image = "/tmp/screen_test.png"
        if Path(test_image).exists():
            print(f"\n📸 测试识别：{test_image}")
            result = ocr.recognize(test_image)
            
            print(f"\n识别结果:")
            print(f"  文本：{result.get('text', 'N/A')}")
            print(f"  置信度：{result.get('confidence', 0):.1f}%")
            print(f"  语言：{result.get('language', 'N/A')}")
            
            if result.get('words'):
                print(f"\n  单词数：{len(result['words'])}")
        else:
            print(f"\n⚠️  测试文件不存在：{test_image}")
    
    print("\n" + "=" * 50)
    print("✅ OCR 文字识别模块测试完成")
