"""
基于向量数据库的记忆服务
支持用户记忆、知识记忆的向量存储和语义检索
"""
import json
import os
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
from app.observability.logger import default_logger as logger
from app.config import settings


class VectorMemoryService:
    """
    基于向量数据库的记忆服务
    使用FAISS进行向量存储，Sentence-BERT进行文本嵌入
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        vector_dim: int = 384,
        memory_dir: str = "vector_memory"
    ):
        """
        初始化向量记忆服务
        
        Args:
            model_name: 句子嵌入模型名称
            vector_dim: 向量维度
            memory_dir: 记忆存储目录
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.vector_dim = vector_dim
        
        # 初始化嵌入模型
        try:
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"已加载嵌入模型: {model_name}")
        except Exception as e:
            logger.error(f"加载嵌入模型失败: {e}")
            # 使用备用模型
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("已使用备用嵌入模型: all-MiniLM-L6-v2")
        
        # 初始化FAISS索引
        self.user_memory_index = None
        self.knowledge_memory_index = None
        self.user_metadata = {}  # 存储用户记忆的元数据
        self.knowledge_metadata = {}  # 存储知识记忆的元数据
        
        # 加载或创建索引
        self._load_or_create_indexes()
        
        logger.info("向量记忆服务初始化完成")
    
    def _load_or_create_indexes(self):
        """加载或创建FAISS索引"""
        user_index_path = self.memory_dir / "user_memory.index"
        knowledge_index_path = self.memory_dir / "knowledge_memory.index"
        user_metadata_path = self.memory_dir / "user_metadata.json"
        knowledge_metadata_path = self.memory_dir / "knowledge_metadata.json"
        
        # 尝试加载用户记忆索引
        if user_index_path.exists():
            self.user_memory_index = faiss.read_index(str(user_index_path))
            if user_metadata_path.exists():
                with open(user_metadata_path, 'r', encoding='utf-8') as f:
                    self.user_metadata = json.load(f)
            logger.info(f"已加载用户记忆索引，包含 {self.user_memory_index.ntotal} 条记录")
        else:
            self.user_memory_index = faiss.IndexFlatIP(self.vector_dim)  # 内积相似度
            self.user_metadata = {}
            logger.info("创建了新的用户记忆索引")
        
        # 尝试加载知识记忆索引
        if knowledge_index_path.exists():
            self.knowledge_memory_index = faiss.read_index(str(knowledge_index_path))
            if knowledge_metadata_path.exists():
                with open(knowledge_metadata_path, 'r', encoding='utf-8') as f:
                    self.knowledge_metadata = json.load(f)
            logger.info(f"已加载知识记忆索引，包含 {self.knowledge_memory_index.ntotal} 条记录")
        else:
            self.knowledge_memory_index = faiss.IndexFlatIP(self.vector_dim)  # 内积相似度
            self.knowledge_metadata = {}
            logger.info("创建了新的知识记忆索引")
    
    def _save_indexes(self):
        """保存FAISS索引和元数据"""
        try:
            # 保存用户记忆索引
            user_index_path = self.memory_dir / "user_memory.index"
            user_metadata_path = self.memory_dir / "user_metadata.json"
            faiss.write_index(self.user_memory_index, str(user_index_path))
            with open(user_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_metadata, f, ensure_ascii=False, indent=2)
            
            # 保存知识记忆索引
            knowledge_index_path = self.memory_dir / "knowledge_memory.index"
            knowledge_metadata_path = self.memory_dir / "knowledge_metadata.json"
            faiss.write_index(self.knowledge_memory_index, str(knowledge_index_path))
            with open(knowledge_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info("向量索引保存成功")
        except Exception as e:
            logger.error(f"保存向量索引失败: {e}")
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        """将文本转换为向量"""
        try:
            vector = self.embedding_model.encode(text, convert_to_numpy=True)
            # 归一化向量，用于内积相似度计算
            vector = vector / np.linalg.norm(vector)
            return vector.astype('float32')
        except Exception as e:
            logger.error(f"文本向量化失败: {e}")
            # 返回零向量
            return np.zeros(self.vector_dim, dtype='float32')
    
    def _vector_to_text(self, vector: np.ndarray) -> str:
        """将向量转换为文本表示（用于调试）"""
        return f"Vector(dim={len(vector)}, norm={np.linalg.norm(vector):.4f})"
    
    # ============ 用户记忆操作 ============
    
    def store_user_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_data: Dict[str, Any]
    ):
        """
        存储用户偏好到向量数据库
        
        Args:
            user_id: 用户ID
            preference_type: 偏好类型
            preference_data: 偏好数据
        """
        try:
            # 构建文本表示
            text_representation = self._preference_to_text(preference_type, preference_data)
            
            # 转换为向量
            vector = self._text_to_vector(text_representation)
            
            # 添加到索引
            index_id = self.user_memory_index.ntotal
            self.user_memory_index.add(np.array([vector]))
            
            # 存储元数据
            self.user_metadata[str(index_id)] = {
                "user_id": user_id,
                "type": "preference",
                "preference_type": preference_type,
                "data": preference_data,
                "text_representation": text_representation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"用户偏好已存储到向量数据库 - UserID: {user_id}, Type: {preference_type}")
        except Exception as e:
            logger.error(f"存储用户偏好失败: {e}")
    
    def store_user_trip(
        self,
        user_id: str,
        trip_data: Dict[str, Any]
    ):
        """
        存储用户行程到向量数据库
        
        Args:
            user_id: 用户ID
            trip_data: 行程数据
        """
        try:
            # 构建文本表示
            text_representation = self._trip_to_text(trip_data)
            
            # 转换为向量
            vector = self._text_to_vector(text_representation)
            
            # 添加到索引
            index_id = self.user_memory_index.ntotal
            self.user_memory_index.add(np.array([vector]))
            
            # 存储元数据
            self.user_metadata[str(index_id)] = {
                "user_id": user_id,
                "type": "trip",
                "data": trip_data,
                "text_representation": text_representation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"用户行程已存储到向量数据库 - UserID: {user_id}")
        except Exception as e:
            logger.error(f"存储用户行程失败: {e}")
    
    def store_user_feedback(
        self,
        user_id: str,
        trip_id: str,
        feedback_data: Dict[str, Any]
    ):
        """
        存储用户反馈到向量数据库
        
        Args:
            user_id: 用户ID
            trip_id: 行程ID
            feedback_data: 反馈数据
        """
        try:
            # 构建文本表示
            text_representation = self._feedback_to_text(feedback_data)
            
            # 转换为向量
            vector = self._text_to_vector(text_representation)
            
            # 添加到索引
            index_id = self.user_memory_index.ntotal
            self.user_memory_index.add(np.array([vector]))
            
            # 存储元数据
            self.user_metadata[str(index_id)] = {
                "user_id": user_id,
                "type": "feedback",
                "trip_id": trip_id,
                "data": feedback_data,
                "text_representation": text_representation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"用户反馈已存储到向量数据库 - UserID: {user_id}, TripID: {trip_id}")
        except Exception as e:
            logger.error(f"存储用户反馈失败: {e}")
    
    def retrieve_user_memories(
        self,
        user_id: str,
        query: str = "",
        limit: int = 10,
        memory_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        基于语义相似度检索用户记忆
        
        Args:
            user_id: 用户ID
            query: 查询文本
            limit: 返回数量限制
            memory_types: 记忆类型过滤，如 ["preference", "trip", "feedback"]
        
        Returns:
            相似的用户记忆列表
        """
        try:
            # 如果没有查询文本，返回用户最近的记忆
            if not query:
                return self._get_recent_user_memories(user_id, limit, memory_types)
            
            # 转换查询为向量
            query_vector = self._text_to_vector(query)
            
            # 在用户记忆中搜索
            distances, indices = self.user_memory_index.search(
                np.array([query_vector]), 
                min(self.user_memory_index.ntotal, limit * 2)  # 搜索更多结果进行过滤
            )
            
            # 过滤结果
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1:  # FAISS返回-1表示无效结果
                    continue
                    
                metadata = self.user_metadata.get(str(idx))
                if not metadata:
                    continue
                
                # 过滤用户ID和记忆类型
                if metadata.get("user_id") != user_id:
                    continue
                    
                if memory_types and metadata.get("type") not in memory_types:
                    continue
                
                # 添加相似度分数
                metadata["similarity_score"] = float(distances[0][i])
                results.append(metadata)
                
                if len(results) >= limit:
                    break
            
            logger.info(f"检索到 {len(results)} 条用户记忆 - UserID: {user_id}, Query: {query}")
            return results
        except Exception as e:
            logger.error(f"检索用户记忆失败: {e}")
            return []
    
    def _get_recent_user_memories(
        self,
        user_id: str,
        limit: int,
        memory_types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """获取用户最近的记忆"""
        user_memories = []
        for metadata in self.user_metadata.values():
            if metadata.get("user_id") != user_id:
                continue
                
            if memory_types and metadata.get("type") not in memory_types:
                continue
                
            user_memories.append(metadata)
        
        # 按时间戳排序
        user_memories.sort(
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        return user_memories[:limit]
    
    # ============ 知识记忆操作 ============
    
    def store_destination_knowledge(
        self,
        destination: str,
        knowledge_data: Dict[str, Any]
    ):
        """
        存储目的地知识到向量数据库
        
        Args:
            destination: 目的地名称
            knowledge_data: 知识数据
        """
        try:
            # 构建文本表示
            text_representation = self._destination_knowledge_to_text(destination, knowledge_data)
            
            # 转换为向量
            vector = self._text_to_vector(text_representation)
            
            # 添加到索引
            index_id = self.knowledge_memory_index.ntotal
            self.knowledge_memory_index.add(np.array([vector]))
            
            # 存储元数据
            self.knowledge_metadata[str(index_id)] = {
                "type": "destination",
                "destination": destination,
                "data": knowledge_data,
                "text_representation": text_representation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"目的地知识已存储到向量数据库 - Destination: {destination}")
        except Exception as e:
            logger.error(f"存储目的地知识失败: {e}")
    
    def store_travel_experience(
        self,
        experience_type: str,
        experience_data: Dict[str, Any]
    ):
        """
        存储旅行经验到向量数据库
        
        Args:
            experience_type: 经验类型
            experience_data: 经验数据
        """
        try:
            # 构建文本表示
            text_representation = self._experience_to_text(experience_type, experience_data)
            
            # 转换为向量
            vector = self._text_to_vector(text_representation)
            
            # 添加到索引
            index_id = self.knowledge_memory_index.ntotal
            self.knowledge_memory_index.add(np.array([vector]))
            
            # 存储元数据
            self.knowledge_metadata[str(index_id)] = {
                "type": "experience",
                "experience_type": experience_type,
                "data": experience_data,
                "text_representation": text_representation,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"旅行经验已存储到向量数据库 - Type: {experience_type}")
        except Exception as e:
            logger.error(f"存储旅行经验失败: {e}")
    
    def retrieve_knowledge_memories(
        self,
        query: str,
        limit: int = 10,
        knowledge_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        基于语义相似度检索知识记忆
        
        Args:
            query: 查询文本
            limit: 返回数量限制
            knowledge_types: 知识类型过滤，如 ["destination", "experience"]
        
        Returns:
            相似的知识记忆列表
        """
        try:
            # 转换查询为向量
            query_vector = self._text_to_vector(query)
            
            # 在知识记忆中搜索
            distances, indices = self.knowledge_memory_index.search(
                np.array([query_vector]), 
                min(self.knowledge_memory_index.ntotal, limit * 2)  # 搜索更多结果进行过滤
            )
            
            # 过滤结果
            results = []
            for i, idx in enumerate(indices[0]):
                if idx == -1:  # FAISS返回-1表示无效结果
                    continue
                    
                metadata = self.knowledge_metadata.get(str(idx))
                if not metadata:
                    continue
                
                # 过滤知识类型
                if knowledge_types and metadata.get("type") not in knowledge_types:
                    continue
                
                # 添加相似度分数
                metadata["similarity_score"] = float(distances[0][i])
                results.append(metadata)
                
                if len(results) >= limit:
                    break
            
            logger.info(f"检索到 {len(results)} 条知识记忆 - Query: {query}")
            return results
        except Exception as e:
            logger.error(f"检索知识记忆失败: {e}")
            return []
    
    # ============ 混合检索 ============
    
    def hybrid_search(
        self,
        user_id: str,
        query: str,
        user_limit: int = 5,
        knowledge_limit: int = 5,
        include_user_memories: bool = True,
        include_knowledge_memories: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        混合检索用户记忆和知识记忆
        
        Args:
            user_id: 用户ID
            query: 查询文本
            user_limit: 用户记忆数量限制
            knowledge_limit: 知识记忆数量限制
            include_user_memories: 是否包含用户记忆
            include_knowledge_memories: 是否包含知识记忆
        
        Returns:
            包含用户记忆和知识记忆的字典
        """
        results = {
            "user_memories": [],
            "knowledge_memories": []
        }
        
        # 检索用户记忆
        if include_user_memories:
            results["user_memories"] = self.retrieve_user_memories(
                user_id, query, user_limit
            )
        
        # 检索知识记忆
        if include_knowledge_memories:
            results["knowledge_memories"] = self.retrieve_knowledge_memories(
                query, knowledge_limit
            )
        
        return results
    
    # ============ 文本转换辅助方法 ============
    
    def _preference_to_text(self, preference_type: str, preference_data: Dict[str, Any]) -> str:
        """将偏好数据转换为文本表示"""
        text_parts = [f"偏好类型: {preference_type}"]
        
        if "destination" in preference_data:
            text_parts.append(f"目的地: {preference_data['destination']}")
        
        if "preferences" in preference_data:
            text_parts.append(f"旅行偏好: {', '.join(preference_data['preferences'])}")
        
        if "hotel_preferences" in preference_data:
            text_parts.append(f"酒店偏好: {', '.join(preference_data['hotel_preferences'])}")
        
        if "budget" in preference_data:
            text_parts.append(f"预算水平: {preference_data['budget']}")
        
        return " ".join(text_parts)
    
    def _trip_to_text(self, trip_data: Dict[str, Any]) -> str:
        """将行程数据转换为文本表示"""
        text_parts = ["旅行行程"]
        
        if "destination" in trip_data:
            text_parts.append(f"目的地: {trip_data['destination']}")
        
        if "start_date" in trip_data and "end_date" in trip_data:
            text_parts.append(f"时间: {trip_data['start_date']} 到 {trip_data['end_date']}")
        
        if "preferences" in trip_data:
            text_parts.append(f"偏好: {', '.join(trip_data['preferences'])}")
        
        if "trip_title" in trip_data:
            text_parts.append(f"行程标题: {trip_data['trip_title']}")
        
        # 添加景点信息
        if "days" in trip_data:
            attractions = []
            for day in trip_data["days"]:
                for attraction in day.get("attractions", []):
                    attractions.append(attraction.get("name", ""))
            if attractions:
                text_parts.append(f"景点: {', '.join(attractions)}")
        
        return " ".join(text_parts)
    
    def _feedback_to_text(self, feedback_data: Dict[str, Any]) -> str:
        """将反馈数据转换为文本表示"""
        text_parts = ["用户反馈"]
        
        if "rating" in feedback_data:
            text_parts.append(f"评分: {feedback_data['rating']}")
        
        if "comments" in feedback_data:
            text_parts.append(f"评论: {feedback_data['comments']}")
        
        if "modifications" in feedback_data:
            text_parts.append(f"修改建议: {feedback_data['modifications']}")
        
        return " ".join(text_parts)
    
    def _destination_knowledge_to_text(self, destination: str, knowledge_data: Dict[str, Any]) -> str:
        """将目的地知识转换为文本表示"""
        text_parts = [f"目的地: {destination}"]
        
        if "description" in knowledge_data:
            text_parts.append(f"描述: {knowledge_data['description']}")
        
        if "highlights" in knowledge_data:
            text_parts.append(f"特色: {', '.join(knowledge_data['highlights'])}")
        
        if "best_season" in knowledge_data:
            text_parts.append(f"最佳季节: {knowledge_data['best_season']}")
        
        if "culture" in knowledge_data:
            text_parts.append(f"文化背景: {knowledge_data['culture']}")
        
        return " ".join(text_parts)
    
    def _experience_to_text(self, experience_type: str, experience_data: Dict[str, Any]) -> str:
        """将经验数据转换为文本表示"""
        text_parts = [f"旅行经验: {experience_type}"]
        
        if "title" in experience_data:
            text_parts.append(f"标题: {experience_data['title']}")
        
        if "description" in experience_data:
            text_parts.append(f"描述: {experience_data['description']}")
        
        if "tags" in experience_data:
            text_parts.append(f"标签: {', '.join(experience_data['tags'])}")
        
        if "destination" in experience_data:
            text_parts.append(f"目的地: {experience_data['destination']}")
        
        return " ".join(text_parts)
    
    # ============ 维护方法 ============
    
    def save(self):
        """保存索引和元数据"""
        self._save_indexes()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆服务统计信息"""
        return {
            "user_memory_count": self.user_memory_index.ntotal,
            "knowledge_memory_count": self.knowledge_memory_index.ntotal,
            "vector_dimension": self.vector_dim,
            "memory_directory": str(self.memory_dir)
        }


# 创建全局向量记忆服务实例
vector_memory_service = VectorMemoryService()