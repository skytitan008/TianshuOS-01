#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检索 API 模块 - Retrieval API Module
基于 Chroma DB 实现向量检索功能
"""

from typing import List, Dict, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalAPI:
    """检索 API 类"""
    
    def __init__(self, vector_store):
        """
        初始化检索 API
        
        Args:
            vector_store: ChromaVectorStore 实例
        """
        self.store = vector_store
        self.client = vector_store.client if vector_store else None
    
    def similarity_search(self, query: str, k: int = 5,
                          collection_name: Optional[str] = None,
                          filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            collection_name: 集合名称
            filter_dict: 过滤条件
            
        Returns:
            搜索结果列表
        """
        if not self.client:
            logger.error("未连接 Chroma DB")
            return []
        
        try:
            # 获取集合
            if collection_name:
                collection = self.client.get_collection(collection_name)
            elif self.store.collection:
                collection = self.store.collection
            else:
                logger.error("未指定集合")
                return []
            
            # 查询
            results = collection.query(
                query_texts=[query],
                n_results=k,
                where=filter_dict,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            formatted = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    formatted.append({
                        "id": results['ids'][0][i],
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else None,
                        "distance": results['distances'][0][i] if results['distances'] else None
                    })
            
            logger.info(f"相似度搜索完成，找到 {len(formatted)} 个结果")
            return formatted
            
        except Exception as e:
            logger.error(f"相似度搜索失败：{e}")
            return []
    
    def get_by_id(self, doc_id: str, 
                  collection_name: Optional[str] = None) -> Optional[Dict]:
        """
        按 ID 获取文档
        
        Args:
            doc_id: 文档 ID
            collection_name: 集合名称
            
        Returns:
            文档信息，不存在返回 None
        """
        if not self.client:
            return None
        
        try:
            if collection_name:
                collection = self.client.get_collection(collection_name)
            elif self.store.collection:
                collection = self.store.collection
            else:
                return None
            
            results = collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"]
            )
            
            if results['documents'] and results['documents'][0]:
                return {
                    "id": results['ids'][0],
                    "text": results['documents'][0],
                    "metadata": results['metadatas'][0] if results['metadatas'] else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文档失败：{e}")
            return None
    
    def delete_by_id(self, doc_id: str,
                     collection_name: Optional[str] = None) -> bool:
        """
        按 ID 删除文档
        
        Args:
            doc_id: 文档 ID
            collection_name: 集合名称
            
        Returns:
            是否成功删除
        """
        if not self.client:
            return False
        
        try:
            if collection_name:
                collection = self.client.get_collection(collection_name)
            elif self.store.collection:
                collection = self.store.collection
            else:
                return False
            
            collection.delete(ids=[doc_id])
            logger.info(f"文档 '{doc_id}' 已删除")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败：{e}")
            return False
    
    def search_with_context(self, query: str, k: int = 3,
                            collection_name: Optional[str] = None) -> Dict:
        """
        带上下文的搜索（用于 AI 引擎）
        
        Args:
            query: 查询文本
            k: 返回结果数量
            collection_name: 集合名称
            
        Returns:
            搜索结果（包含上下文）
        """
        results = self.similarity_search(query, k, collection_name)
        
        return {
            "query": query,
            "results": results,
            "context": "\n".join([r['text'] for r in results]) if results else "",
            "result_count": len(results)
        }


def main():
    """测试检索 API"""
    print("=" * 60)
    print("检索 API 模块测试")
    print("=" * 60)
    
    from vector_store import ChromaVectorStore
    
    # 创建实例
    store = ChromaVectorStore(host="localhost", port=8000)
    
    if store.connect():
        api = RetrievalAPI(store)
        
        # 测试搜索
        print("\n测试相似度搜索:")
        results = api.similarity_search(
            query="天枢 OS",
            k=2,
            collection_name="test_collection"
        )
        
        for i, r in enumerate(results, 1):
            print(f"  {i}. {r['text']} (距离：{r['distance']:.4f})")
        
        store.close()
    
    print("\n测试完成")


if __name__ == '__main__':
    main()
