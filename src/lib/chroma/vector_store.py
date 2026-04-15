#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量存储模块 - Vector Store Module
基于 Chroma DB 实现向量存储功能
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Chroma DB 向量存储类"""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        初始化 Chroma DB 连接
        
        Args:
            host: Chroma DB 主机地址
            port: Chroma DB 端口
        """
        self.host = host
        self.port = port
        self.client: Optional[chromadb.Client] = None
        self.collection = None
    
    def connect(self) -> bool:
        """
        连接 Chroma DB
        
        Returns:
            是否成功连接
        """
        try:
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 测试连接
            self.client.heartbeat()
            logger.info(f"已连接到 Chroma DB (http://{self.host}:{self.port})")
            return True
            
        except Exception as e:
            logger.error(f"连接 Chroma DB 失败：{e}")
            return False
    
    def create_collection(self, name: str, 
                          metadata: Optional[Dict] = None) -> bool:
        """
        创建集合
        
        Args:
            name: 集合名称
            metadata: 集合元数据
            
        Returns:
            是否成功创建
        """
        if not self.client:
            logger.error("未连接 Chroma DB")
            return False
        
        try:
            # 如果集合已存在，先删除
            existing = self.client.list_collections()
            if name in [c.name for c in existing]:
                self.client.delete_collection(name)
                logger.info(f"已删除已存在的集合：{name}")
            
            self.collection = self.client.create_collection(
                name=name,
                metadata=metadata
            )
            logger.info(f"集合 '{name}' 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建集合失败：{e}")
            return False
    
    def add_documents(self, texts: List[str], 
                      metadatas: Optional[List[Dict]] = None,
                      ids: Optional[List[str]] = None,
                      collection_name: Optional[str] = None) -> bool:
        """
        添加文档到向量库
        
        Args:
            texts: 文档文本列表
            metadatas: 元数据列表
            ids: 文档 ID 列表
            collection_name: 集合名称（可选，使用当前集合）
            
        Returns:
            是否成功添加
        """
        if not self.collection and not collection_name:
            logger.error("未选择集合")
            return False
        
        try:
            # 使用指定集合或当前集合
            if collection_name:
                collection = self.client.get_collection(collection_name)
            else:
                collection = self.collection
            
            # 生成 ID（如果未提供）
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(texts))]
            
            # 添加文档
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"成功添加 {len(texts)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"添加文档失败：{e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """
        删除集合
        
        Args:
            name: 集合名称
            
        Returns:
            是否成功删除
        """
        if not self.client:
            logger.error("未连接 Chroma DB")
            return False
        
        try:
            self.client.delete_collection(name)
            logger.info(f"集合 '{name}' 已删除")
            return True
        except Exception as e:
            logger.error(f"删除集合失败：{e}")
            return False
    
    def get_collection_stats(self, name: str) -> Dict:
        """
        获取集合统计信息
        
        Args:
            name: 集合名称
            
        Returns:
            统计信息字典
        """
        if not self.client:
            return {}
        
        try:
            collection = self.client.get_collection(name)
            count = collection.count()
            
            return {
                "name": name,
                "document_count": count,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"获取统计信息失败：{e}")
            return {}
    
    def close(self):
        """关闭连接"""
        self.client = None
        self.collection = None
        logger.info("已关闭 Chroma DB 连接")


def main():
    """测试向量存储"""
    print("=" * 60)
    print("向量存储模块测试")
    print("=" * 60)
    
    # 创建实例
    store = ChromaVectorStore(host="localhost", port=8000)
    
    # 连接
    if store.connect():
        print("✅ 连接成功")
        
        # 创建集合
        if store.create_collection("test_collection"):
            print("✅ 集合创建成功")
            
            # 添加文档
            texts = [
                "天枢 OS 是一个智能操作系统",
                "Chroma DB 是向量数据库",
                "AI 引擎支持长期记忆"
            ]
            metadatas = [
                {"type": "os"},
                {"type": "database"},
                {"type": "ai"}
            ]
            
            if store.add_documents(texts, metadatas):
                print("✅ 文档添加成功")
                
                # 获取统计
                stats = store.get_collection_stats("test_collection")
                print(f"📊 集合统计：{stats}")
        
        store.close()
    
    print("\n测试完成")


if __name__ == '__main__':
    main()
