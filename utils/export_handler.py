"""
导出处理器模块
提供图像导出、数据导出、报告生成、分享链接等功能
"""
import os
import json
import csv
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
from io import BytesIO, StringIO
import base64

from utils.db_connector import Neo4jConnector
from config import EXPORT_CONFIG, SHARE_CONFIG

logger = logging.getLogger(__name__)

class ExportHandler:
    """导出处理器类"""
    
    def __init__(self, db_connector: Neo4jConnector):
        self.db = db_connector
        self.export_dir = EXPORT_CONFIG.get("export_dir", "static/exports")
        self.allowed_formats = EXPORT_CONFIG.get("allowed_formats", ["png", "svg", "pdf", "json", "csv", "xlsx"])
        self.max_file_size = EXPORT_CONFIG.get("max_file_size", "50MB")
        self.link_expiry_days = SHARE_CONFIG.get("link_expiry_days", 7)
        self.max_share_links = SHARE_CONFIG.get("max_share_links", 100)
        
        # 确保导出目录存在
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_graph_data(self, nodes: List[Dict], edges: List[Dict], 
                         format_type: str = "json", filename: Optional[str] = None) -> Tuple[bool, str, Optional[bytes]]:
        """
        导出图谱数据
        
        Args:
            nodes: 节点列表
            edges: 边列表
            format_type: 导出格式 ("json", "csv", "xlsx")
            filename: 文件名（可选）
            
        Returns:
            (成功标志, 消息, 文件数据)
        """
        try:
            if format_type not in self.allowed_formats:
                return False, f"不支持的导出格式: {format_type}", None
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"knowledge_graph_{timestamp}"
            
            if format_type == "json":
                return self._export_json(nodes, edges, filename)
            elif format_type == "csv":
                return self._export_csv(nodes, edges, filename)
            elif format_type == "xlsx":
                return self._export_xlsx(nodes, edges, filename)
            else:
                return False, f"暂不支持 {format_type} 格式导出", None
                
        except Exception as e:
            logger.error(f"导出图谱数据失败: {str(e)}")
            return False, f"导出失败: {str(e)}", None
    
    def export_analysis_report(self, analysis_data: Dict, format_type: str = "json", 
                             filename: Optional[str] = None) -> Tuple[bool, str, Optional[bytes]]:
        """
        导出分析报告
        
        Args:
            analysis_data: 分析数据
            format_type: 导出格式
            filename: 文件名
            
        Returns:
            (成功标志, 消息, 文件数据)
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"analysis_report_{timestamp}"
            
            if format_type == "json":
                json_data = json.dumps(analysis_data, ensure_ascii=False, indent=2)
                file_data = json_data.encode('utf-8')
                return True, f"成功导出分析报告", file_data
            
            elif format_type == "csv":
                # 将分析数据转换为CSV格式
                csv_data = self._convert_analysis_to_csv(analysis_data)
                return True, f"成功导出分析报告", csv_data
            
            elif format_type == "xlsx":
                # 将分析数据转换为Excel格式
                excel_data = self._convert_analysis_to_excel(analysis_data)
                return True, f"成功导出分析报告", excel_data
            
            else:
                return False, f"不支持的报告格式: {format_type}", None
                
        except Exception as e:
            logger.error(f"导出分析报告失败: {str(e)}")
            return False, f"导出失败: {str(e)}", None
    
    def create_share_link(self, graph_config: Dict, title: str = "知识图谱分享") -> Tuple[bool, str, Optional[str]]:
        """
        创建分享链接
        
        Args:
            graph_config: 图谱配置数据
            title: 分享标题
            
        Returns:
            (成功标志, 消息, 分享ID)
        """
        try:
            # 生成唯一的分享ID
            share_id = str(uuid.uuid4())
            
            # 计算过期时间
            expires_at = datetime.now() + timedelta(days=self.link_expiry_days)
            
            # 存储分享配置到数据库
            share_query = """
            CREATE (sc:ShareConfig {
                share_id: $share_id,
                title: $title,
                graph_config: $graph_config,
                created_time: datetime(),
                expires_at: datetime($expires_at),
                access_count: 0
            })
            """
            
            self.db.query(share_query, {
                "share_id": share_id,
                "title": title,
                "graph_config": json.dumps(graph_config, ensure_ascii=False),
                "expires_at": expires_at.isoformat()
            })
            
            # 清理过期的分享链接
            self._cleanup_expired_shares()
            
            logger.info(f"创建分享链接成功: {share_id}")
            return True, f"分享链接创建成功，有效期{self.link_expiry_days}天", share_id
            
        except Exception as e:
            logger.error(f"创建分享链接失败: {str(e)}")
            return False, f"创建分享链接失败: {str(e)}", None
    
    def get_share_config(self, share_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        获取分享配置
        
        Args:
            share_id: 分享ID
            
        Returns:
            (成功标志, 消息, 配置数据)
        """
        try:
            query = """
            MATCH (sc:ShareConfig {share_id: $share_id})
            WHERE sc.expires_at > datetime()
            SET sc.access_count = sc.access_count + 1
            RETURN sc.title as title,
                   sc.graph_config as graph_config,
                   sc.created_time as created_time,
                   sc.expires_at as expires_at,
                   sc.access_count as access_count
            """
            
            results = self.db.query(query, {"share_id": share_id})
            
            if results:
                result = results[0]
                config_data = {
                    "title": result["title"],
                    "graph_config": json.loads(result["graph_config"]),
                    "created_time": result["created_time"],
                    "expires_at": result["expires_at"],
                    "access_count": result["access_count"]
                }
                return True, "获取分享配置成功", config_data
            else:
                return False, "分享链接不存在或已过期", None
                
        except Exception as e:
            logger.error(f"获取分享配置失败: {str(e)}")
            return False, f"获取分享配置失败: {str(e)}", None
    
    def export_entity_details(self, entity_name: str, entity_type: str, 
                            format_type: str = "json") -> Tuple[bool, str, Optional[bytes]]:
        """
        导出实体详细信息
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            format_type: 导出格式
            
        Returns:
            (成功标志, 消息, 文件数据)
        """
        try:
            # 查询实体详细信息
            detail_query = f"""
            MATCH (n:{entity_type} {{name: $name}})
            OPTIONAL MATCH (n)-[r]-(related)
            RETURN n as entity,
                   collect({{
                       related_entity: related,
                       relationship: r,
                       relationship_type: type(r)
                   }}) as relationships
            """
            
            results = self.db.query(detail_query, {"name": entity_name})
            
            if not results:
                return False, f"未找到实体: {entity_name}", None
            
            result = results[0]
            entity_data = {
                "entity_name": entity_name,
                "entity_type": entity_type,
                "entity_properties": dict(result["entity"]),
                "relationships": []
            }
            
            # 处理关系数据
            for rel_data in result["relationships"]:
                if rel_data["related_entity"]:
                    relationship_info = {
                        "related_entity_name": rel_data["related_entity"].get("name", ""),
                        "related_entity_type": list(rel_data["related_entity"].labels)[0] if rel_data["related_entity"].labels else "",
                        "relationship_type": rel_data["relationship_type"],
                        "relationship_properties": dict(rel_data["relationship"]) if rel_data["relationship"] else {}
                    }
                    entity_data["relationships"].append(relationship_info)
            
            # 导出数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{entity_name}_details_{timestamp}"
            
            if format_type == "json":
                json_data = json.dumps(entity_data, ensure_ascii=False, indent=2)
                file_data = json_data.encode('utf-8')
                return True, f"成功导出 {entity_name} 的详细信息", file_data
            
            elif format_type == "csv":
                # 转换为CSV格式
                csv_buffer = StringIO()
                
                # 写入实体基本信息
                csv_buffer.write("实体信息\n")
                csv_buffer.write(f"名称,{entity_name}\n")
                csv_buffer.write(f"类型,{entity_type}\n")
                csv_buffer.write(f"描述,{entity_data['entity_properties'].get('description', '')}\n")
                csv_buffer.write("\n关系信息\n")
                csv_buffer.write("相关实体,实体类型,关系类型\n")
                
                for rel in entity_data["relationships"]:
                    csv_buffer.write(f"{rel['related_entity_name']},{rel['related_entity_type']},{rel['relationship_type']}\n")
                
                file_data = csv_buffer.getvalue().encode('utf-8')
                return True, f"成功导出 {entity_name} 的详细信息", file_data
            
            else:
                return False, f"不支持的格式: {format_type}", None
                
        except Exception as e:
            logger.error(f"导出实体详情失败: {str(e)}")
            return False, f"导出失败: {str(e)}", None
    
    def get_export_statistics(self) -> Dict:
        """
        获取导出统计信息
        
        Returns:
            导出统计数据
        """
        try:
            # 获取分享链接统计
            share_stats_query = """
            MATCH (sc:ShareConfig)
            WHERE sc.expires_at > datetime()
            RETURN count(sc) as active_shares,
                   sum(sc.access_count) as total_accesses,
                   avg(sc.access_count) as avg_accesses
            """
            
            share_results = self.db.query(share_stats_query)
            
            stats = {
                "active_shares": 0,
                "total_accesses": 0,
                "avg_accesses": 0,
                "export_formats_supported": self.allowed_formats,
                "max_file_size": self.max_file_size,
                "link_expiry_days": self.link_expiry_days
            }
            
            if share_results:
                result = share_results[0]
                stats.update({
                    "active_shares": result.get("active_shares", 0),
                    "total_accesses": result.get("total_accesses", 0),
                    "avg_accesses": result.get("avg_accesses", 0)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取导出统计失败: {str(e)}")
            return {}
    
    def _export_json(self, nodes: List[Dict], edges: List[Dict], filename: str) -> Tuple[bool, str, bytes]:
        """导出JSON格式"""
        data = {
            "nodes": nodes,
            "edges": edges,
            "exported_at": datetime.now().isoformat(),
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        file_data = json_data.encode('utf-8')
        
        return True, f"成功导出 {len(nodes)} 个节点和 {len(edges)} 条边", file_data
    
    def _export_csv(self, nodes: List[Dict], edges: List[Dict], filename: str) -> Tuple[bool, str, bytes]:
        """导出CSV格式"""
        csv_buffer = StringIO()
        
        # 写入节点数据
        csv_buffer.write("节点数据\n")
        csv_buffer.write("ID,标签,类型,其他属性\n")
        
        for node in nodes:
            node_id = node.get("id", "")
            label = node.get("label", "")
            group = node.get("group", "")
            other_props = {k: v for k, v in node.items() if k not in ["id", "label", "group"]}
            other_props_str = json.dumps(other_props, ensure_ascii=False) if other_props else ""
            
            csv_buffer.write(f'"{node_id}","{label}","{group}","{other_props_str}"\n')
        
        # 写入边数据
        csv_buffer.write("\n边数据\n")
        csv_buffer.write("源节点,目标节点,关系类型,其他属性\n")
        
        for edge in edges:
            from_node = edge.get("from", "")
            to_node = edge.get("to", "")
            label = edge.get("label", "")
            other_props = {k: v for k, v in edge.items() if k not in ["from", "to", "label"]}
            other_props_str = json.dumps(other_props, ensure_ascii=False) if other_props else ""
            
            csv_buffer.write(f'"{from_node}","{to_node}","{label}","{other_props_str}"\n')
        
        file_data = csv_buffer.getvalue().encode('utf-8')
        return True, f"成功导出 {len(nodes)} 个节点和 {len(edges)} 条边", file_data
    
    def _export_xlsx(self, nodes: List[Dict], edges: List[Dict], filename: str) -> Tuple[bool, str, bytes]:
        """导出Excel格式"""
        try:
            # 创建Excel文件
            excel_buffer = BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # 节点数据表
                nodes_df = pd.DataFrame(nodes)
                if not nodes_df.empty:
                    nodes_df.to_excel(writer, sheet_name='节点数据', index=False)
                
                # 边数据表
                edges_df = pd.DataFrame(edges)
                if not edges_df.empty:
                    edges_df.to_excel(writer, sheet_name='边数据', index=False)
                
                # 统计信息表
                stats_data = {
                    '指标': ['节点总数', '边总数', '导出时间'],
                    '数值': [len(nodes), len(edges), datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                }
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='统计信息', index=False)
            
            file_data = excel_buffer.getvalue()
            return True, f"成功导出 {len(nodes)} 个节点和 {len(edges)} 条边", file_data
            
        except ImportError:
            return False, "缺少openpyxl库，无法导出Excel格式", None
        except Exception as e:
            return False, f"导出Excel失败: {str(e)}", None
    
    def _convert_analysis_to_csv(self, analysis_data: Dict) -> bytes:
        """将分析数据转换为CSV格式"""
        csv_buffer = StringIO()
        
        csv_buffer.write("知识图谱分析报告\n")
        csv_buffer.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 处理不同类型的分析数据
        for section, data in analysis_data.items():
            csv_buffer.write(f"{section}\n")
            
            if isinstance(data, dict):
                for key, value in data.items():
                    csv_buffer.write(f"{key},{value}\n")
            elif isinstance(data, list):
                if data and isinstance(data[0], dict):
                    # 写入表头
                    headers = list(data[0].keys())
                    csv_buffer.write(",".join(headers) + "\n")
                    
                    # 写入数据
                    for item in data:
                        values = [str(item.get(header, "")) for header in headers]
                        csv_buffer.write(",".join(values) + "\n")
            else:
                csv_buffer.write(f"{data}\n")
            
            csv_buffer.write("\n")
        
        return csv_buffer.getvalue().encode('utf-8')
    
    def _convert_analysis_to_excel(self, analysis_data: Dict) -> bytes:
        """将分析数据转换为Excel格式"""
        try:
            excel_buffer = BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                sheet_count = 0
                
                for section, data in analysis_data.items():
                    sheet_name = section[:31]  # Excel工作表名称限制
                    
                    if isinstance(data, dict):
                        # 字典数据转换为DataFrame
                        df = pd.DataFrame(list(data.items()), columns=['指标', '数值'])
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    elif isinstance(data, list) and data and isinstance(data[0], dict):
                        # 列表字典数据直接转换
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    else:
                        # 其他数据类型
                        df = pd.DataFrame({'数据': [str(data)]})
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    sheet_count += 1
                    if sheet_count >= 10:  # 限制工作表数量
                        break
            
            return excel_buffer.getvalue()
            
        except ImportError:
            # 如果没有openpyxl，返回CSV格式
            return self._convert_analysis_to_csv(analysis_data)
        except Exception as e:
            logger.error(f"转换Excel失败: {str(e)}")
            return self._convert_analysis_to_csv(analysis_data)
    
    def _cleanup_expired_shares(self):
        """清理过期的分享链接"""
        try:
            cleanup_query = """
            MATCH (sc:ShareConfig)
            WHERE sc.expires_at < datetime()
            DELETE sc
            """
            
            self.db.query(cleanup_query)
            
            # 限制分享链接总数
            limit_query = """
            MATCH (sc:ShareConfig)
            WITH sc ORDER BY sc.created_time DESC
            SKIP $max_links
            DELETE sc
            """
            
            self.db.query(limit_query, {"max_links": self.max_share_links})
            
        except Exception as e:
            logger.error(f"清理过期分享链接失败: {str(e)}")