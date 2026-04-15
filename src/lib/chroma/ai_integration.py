#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 引擎集成模块 - AI Integration Module
将 Chroma DB 长期记忆与天枢 OS AI 引擎集成
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    metadata: Dict
    created_at: str


class AIIntegration:
    """AI 引擎集成类"""
    
    def __init__(self, vector_store, retrieval_api):
        """
        初始化 AI 集成
        
        Args:
            vector_store: ChromaVectorStore 实例
            retrieval_api: RetrievalAPI 实例
        """
        self.store = vector_store
        self.api = retrieval_api
        self.collection_name = "ai_memory"
    
    def initialize(self) -> bool:
        """
        初始化 AI 记忆系统
        
        Returns:
            是否成功初始化
        """
        if not self.store.connect():
            return False
        
        if not self.store.create_collection(self.collection_name):
            return False
        
        logger.info("AI 记忆系统初始化成功")
        return True
    
    def store_memory(self, content: str, metadata: Optional[Dict] = None,
                     memory_id: Optional[str] = None) -> Optional[str]:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            metadata: 元数据
            memory_id: 记忆 ID（可选）
            
        Returns:
            记忆 ID，失败返回 None
        """
        import time
        
        if memory_id is None:
            memory_id = f"mem_{int(time.time() * 1000)}"
        
        if metadata is None:
            metadata = {}
        
        # 添加时间戳
        metadata['created_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
        metadata['type'] = 'ai_memory'
        
        if self.store.add_documents(
            texts=[content],
            metadatas=[metadata],
            ids=[memory_id],
            collection_name=self.collection_name
        ):
            logger.info(f"记忆已存储：{memory_id}")
            return memory_id
        
        return None
    
    def retrieve_memory(self, query: str, k: int = 5) -> List[MemoryItem]:
        """
        检索记忆
        
        Args:
            query: 查询文本
            k: 返回数量
            
        Returns:
            记忆项列表
        """
        results = self.api.similarity_search(
            query=query,
            k=k,
            collection_name=self.collection_name
        )
        
        memories = []
        for r in results:
            memories.append(MemoryItem(
                id=r['id'],
                content=r['text'],
                metadata=r.get('metadata', {}),
                created_at=r.get('metadata', {}).get('created_at', '')
            ))
        
        logger.info(f"检索到 {len(memories)} 条记忆")
        return memories
    
    def get_context_for_ai(self, query: str, k: int = 3) -> str:
        """
        为 AI 引擎获取上下文
        
        Args:
            query: 当前查询
            k: 上下文数量
            
        Returns:
            上下文文本
        """
        result = self.api.search_with_context(
            query=query,
            k=k,
            collection_name=self.collection_name
        )
        
        return result.get('context', '')
    
    def enhance_ai_response(self, query: str, ai_response: str) -> str:
        """
        增强 AI 响应（添加记忆上下文）
        
        Args:
            query: 用户查询
            ai_response: AI 原始响应
            
        Returns:
            增强后的响应
        """
        context = self.get_context_for_ai(query, k=3)
        
        if context:
            enhanced = f"""{ai_response}

---
**相关记忆**:
{context}
"""
            return enhanced
        
        return ai_response
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            是否成功删除
        """
        return self.api.delete_by_id(
            doc_id=memory_id,
            collection_name=self.collection_name
        )
    
    def list_memories(self, limit: int = 10) -> List[MemoryItem]:
        """
        列出记忆
        
        Args:
            limit: 数量限制
            
        Returns:
            记忆项列表
        """
        if not self.store.client:
            return []
        
        try:
            collection = self.store.client.get_collection(self.collection_name)
            results = collection.get(include=["documents", "metadatas"], limit=limit)
            
            memories = []
            for i, doc in enumerate(results.get('documents', [])):
                memories.append(MemoryItem(
                    id=results['ids'][i],
                    content=doc,
                    metadata=results.get('metadatas', [{}])[i],
                    created_at=results.get('metadatas', [{}])[i].get('created_at', '')
                ))
            
            return memories
            
        except Exception as e:
            logger.error(f"列出记忆失败：{e}")
            return []
    
    def get_stats(self) -> Dict:
        """
        获取记忆系统统计
        
        Returns:
            统计信息
        """
        return self.store.get_collection_stats(self.collection_name)


def main():
    """测试 AI 集成"""
    print("=" * 60)
    print("AI 引擎集成模块测试")
    print("=" * 60)
    
    from vector_store import ChromaVectorStore
    from retrieval_api import RetrievalAPI
    
    # 创建实例
    store = ChromaVectorStore(host="localhost", port=8000)
    api = RetrievalAPI(store)
    integration = AIIntegration(store, api)
    
    # 初始化
    if integration.initialize():
        print("✅ AI 记忆系统初始化成功")
        
        # 存储记忆
        mem_id = integration.store_memory(
            content="天枢 OS 支持 AI 长期记忆功能",
            metadata={"category": "feature"}
        )
        print(f"✅ 记忆存储成功：{mem_id}")
        
        # 检索记忆
        memories = integration.retrieve_memory("天枢 OS", k=2)
        print(f"📊 检索到 {len(memories)} 条记忆:")
        for m in memories:
            print(f"  - {m.content[:50]}...")
        
        # 获取统计
        stats = integration.get_stats()
        print(f"📈 统计：{stats}")
        
        # 获取 AI 上下文
        context = integration.get_context_for_ai("天枢 OS 功能")
        print(f"📝 AI 上下文：{context[:100]}...")
    
    print("\n测试完成")


if __name__ == '__main__':
    main()
