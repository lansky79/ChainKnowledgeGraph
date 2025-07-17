"""
实体详情组件
提供实体信息展示、编辑、关系管理等功能
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from utils.db_connector import Neo4jConnector
from utils.logger import setup_logger

logger = setup_logger("EntityDetail")

class EntityDetail:
    """实体详情组件类"""
    
    def __init__(self, db_connector: Neo4jConnector):
        self.db = db_connector
    
    def display_entity_info(self, entity_name: str, entity_type: str, 
                           editable: bool = False) -> Dict[str, Any]:
        """
        显示实体信息
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            editable: 是否可编辑
            
        Returns:
            实体信息字典
        """
        try:
            # 查询实体信息
            query = f"""
            MATCH (n:{entity_type} {{name: $name}})
            RETURN n
            """
            
            results = self.db.query(query, {"name": entity_name})
            
            if not results:
                st.error(f"未找到实体: {entity_name}")
                return {}
            
            entity = results[0]["n"]
            entity_props = dict(entity)
            
            if editable:
                return self._display_editable_info(entity_name, entity_type, entity_props)
            else:
                return self._display_readonly_info(entity_name, entity_type, entity_props)
                
        except Exception as e:
            logger.error(f"显示实体信息失败: {str(e)}")
            st.error(f"显示实体信息失败: {str(e)}")
            return {}
    
    def _display_readonly_info(self, entity_name: str, entity_type: str, 
                              entity_props: Dict) -> Dict[str, Any]:
        """显示只读实体信息"""
        st.subheader(f"📋 {entity_name} 详细信息")
        
        # 基本信息
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("**基本属性:**")
            st.write(f"- **名称**: {entity_props.get('name', '未知')}")
            st.write(f"- **类型**: {self._get_type_display_name(entity_type)}")
            
            # 显示其他属性
            for key, value in entity_props.items():
                if key not in ['name']:
                    st.write(f"- **{key}**: {value}")
        
        with col2:
            # 显示关系统计
            self._display_relationship_stats(entity_name, entity_type)
        
        return entity_props
    
    def _display_editable_info(self, entity_name: str, entity_type: str, 
                              entity_props: Dict) -> Dict[str, Any]:
        """显示可编辑实体信息"""
        st.subheader(f"✏️ 编辑 {entity_name}")
        
        # 创建编辑表单
        with st.form(f"edit_entity_{entity_name}"):
            st.write("**编辑实体属性:**")
            
            # 名称（通常不允许修改）
            new_name = st.text_input("名称", value=entity_props.get('name', ''), disabled=True)
            
            # 描述
            new_description = st.text_area(
                "描述", 
                value=entity_props.get('description', ''),
                height=100,
                help="实体的详细描述信息"
            )
            
            # 其他可编辑属性
            other_props = {}
            for key, value in entity_props.items():
                if key not in ['name', 'description']:
                    if isinstance(value, str):
                        other_props[key] = st.text_input(f"{key}", value=value)
                    elif isinstance(value, (int, float)):
                        other_props[key] = st.number_input(f"{key}", value=value)
                    else:
                        other_props[key] = st.text_input(f"{key}", value=str(value))
            
            # 添加新属性
            st.write("**添加新属性:**")
            col1, col2 = st.columns(2)
            with col1:
                new_prop_key = st.text_input("属性名", key=f"new_prop_key_{entity_name}")
            with col2:
                new_prop_value = st.text_input("属性值", key=f"new_prop_value_{entity_name}")
            
            # 提交按钮
            submitted = st.form_submit_button("💾 保存修改")
            
            if submitted:
                # 构建更新的属性字典
                updated_props = {
                    'name': new_name,
                    'description': new_description,
                    **other_props
                }
                
                # 添加新属性
                if new_prop_key and new_prop_value:
                    updated_props[new_prop_key] = new_prop_value
                
                # 更新实体
                success = self._update_entity(entity_name, entity_type, updated_props)
                
                if success:
                    st.success("✅ 实体信息更新成功！")
                    st.rerun()
                else:
                    st.error("❌ 更新失败，请重试")
        
        return entity_props
    
    def display_entity_relationships(self, entity_name: str, entity_type: str, 
                                   editable: bool = False) -> List[Dict]:
        """
        显示实体关系
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            editable: 是否可编辑
            
        Returns:
            关系列表
        """
        try:
            # 查询实体关系
            query = f"""
            MATCH (n:{entity_type} {{name: $name}})-[r]-(related)
            RETURN type(r) as relationship_type,
                   related.name as related_name,
                   labels(related)[0] as related_type,
                   r as relationship,
                   related as related_entity,
                   CASE WHEN startNode(r) = n THEN 'outgoing' ELSE 'incoming' END as direction
            ORDER BY relationship_type, related_name
            """
            
            results = self.db.query(query, {"name": entity_name})
            
            if not results:
                st.info("该实体暂无关系")
                return []
            
            # 处理关系数据
            relationships = []
            for result in results:
                relationships.append({
                    'relationship_type': result['relationship_type'],
                    'related_name': result['related_name'],
                    'related_type': result['related_type'],
                    'direction': result['direction'],
                    'relationship_props': dict(result['relationship']) if result['relationship'] else {}
                })
            
            # 显示关系
            if editable:
                self._display_editable_relationships(entity_name, entity_type, relationships)
            else:
                self._display_readonly_relationships(relationships)
            
            return relationships
            
        except Exception as e:
            logger.error(f"显示实体关系失败: {str(e)}")
            st.error(f"显示实体关系失败: {str(e)}")
            return []
    
    def _display_readonly_relationships(self, relationships: List[Dict]):
        """显示只读关系信息"""
        st.subheader("🔗 实体关系")
        
        if not relationships:
            st.info("暂无关系数据")
            return
        
        # 按关系类型分组
        grouped_rels = {}
        for rel in relationships:
            rel_type = rel['relationship_type']
            if rel_type not in grouped_rels:
                grouped_rels[rel_type] = []
            grouped_rels[rel_type].append(rel)
        
        # 显示分组关系
        for rel_type, rels in grouped_rels.items():
            with st.expander(f"{rel_type} ({len(rels)}个)", expanded=True):
                for rel in rels:
                    direction_icon = "→" if rel['direction'] == 'outgoing' else "←"
                    type_display = self._get_type_display_name(rel['related_type'])
                    
                    st.write(f"{direction_icon} **{rel['related_name']}** ({type_display})")
    
    def _display_editable_relationships(self, entity_name: str, entity_type: str, 
                                      relationships: List[Dict]):
        """显示可编辑关系信息"""
        st.subheader("🔗 管理实体关系")
        
        # 现有关系管理
        if relationships:
            st.write("**现有关系:**")
            
            for i, rel in enumerate(relationships):
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        direction_icon = "→" if rel['direction'] == 'outgoing' else "←"
                        type_display = self._get_type_display_name(rel['related_type'])
                        st.write(f"{direction_icon} **{rel['related_name']}** ({type_display}) - {rel['relationship_type']}")
                    
                    with col2:
                        if st.button("编辑", key=f"edit_rel_{i}"):
                            st.session_state[f"editing_rel_{i}"] = True
                    
                    with col3:
                        if st.button("删除", key=f"delete_rel_{i}", type="secondary"):
                            if self._delete_relationship(entity_name, entity_type, rel):
                                st.success("关系删除成功")
                                st.rerun()
                            else:
                                st.error("删除失败")
                    
                    # 编辑关系表单
                    if st.session_state.get(f"editing_rel_{i}", False):
                        with st.form(f"edit_relationship_{i}"):
                            st.write("编辑关系:")
                            new_rel_type = st.text_input("关系类型", value=rel['relationship_type'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("保存"):
                                    if self._update_relationship(entity_name, entity_type, rel, new_rel_type):
                                        st.success("关系更新成功")
                                        st.session_state[f"editing_rel_{i}"] = False
                                        st.rerun()
                                    else:
                                        st.error("更新失败")
                            
                            with col2:
                                if st.form_submit_button("取消"):
                                    st.session_state[f"editing_rel_{i}"] = False
                                    st.rerun()
                    
                    st.markdown("---")
        
        # 添加新关系
        st.write("**添加新关系:**")
        self._display_add_relationship_form(entity_name, entity_type)
    
    def _display_add_relationship_form(self, entity_name: str, entity_type: str):
        """显示添加关系表单"""
        with st.form(f"add_relationship_{entity_name}"):
            st.write("创建新关系:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                target_type = st.selectbox(
                    "目标实体类型",
                    ["company", "industry", "product"],
                    format_func=lambda x: self._get_type_display_name(x)
                )
                
                relationship_type = st.selectbox(
                    "关系类型",
                    ["所属行业", "主营产品", "上级行业", "上游材料", "合作关系", "竞争关系"]
                )
            
            with col2:
                # 获取目标实体列表
                target_entities = self._get_entities_by_type(target_type)
                target_entity = st.selectbox(
                    "目标实体",
                    target_entities if target_entities else ["无可用实体"]
                )
                
                direction = st.selectbox(
                    "关系方向",
                    ["outgoing", "incoming"],
                    format_func=lambda x: "指向目标实体" if x == "outgoing" else "来自目标实体"
                )
            
            if st.form_submit_button("➕ 添加关系"):
                if target_entity and target_entity != "无可用实体":
                    success = self._create_relationship(
                        entity_name, entity_type, 
                        target_entity, target_type,
                        relationship_type, direction
                    )
                    
                    if success:
                        st.success("关系添加成功！")
                        st.rerun()
                    else:
                        st.error("添加关系失败")
                else:
                    st.warning("请选择有效的目标实体")
    
    def manage_entity_batch_operations(self, entity_type: str) -> bool:
        """
        批量操作管理
        
        Args:
            entity_type: 实体类型
            
        Returns:
            操作是否成功
        """
        st.subheader(f"📦 批量管理{self._get_type_display_name(entity_type)}")
        
        try:
            # 获取实体列表
            entities = self._get_entities_by_type(entity_type, with_details=True)
            
            if not entities:
                st.info(f"暂无{self._get_type_display_name(entity_type)}数据")
                return False
            
            # 创建数据框
            df = pd.DataFrame(entities)
            
            # 显示实体列表
            st.write("**选择要操作的实体:**")
            
            # 使用数据编辑器进行批量选择
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                key=f"batch_edit_{entity_type}"
            )
            
            # 批量操作选项
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🏷️ 批量添加标签"):
                    self._batch_add_tags(entity_type, edited_df)
            
            with col2:
                if st.button("📝 批量更新描述"):
                    self._batch_update_descriptions(entity_type, edited_df)
            
            with col3:
                if st.button("🗑️ 批量删除", type="secondary"):
                    self._batch_delete_entities(entity_type, edited_df)
            
            return True
            
        except Exception as e:
            logger.error(f"批量操作失败: {str(e)}")
            st.error(f"批量操作失败: {str(e)}")
            return False
    
    def _update_entity(self, entity_name: str, entity_type: str, 
                      updated_props: Dict[str, Any]) -> bool:
        """更新实体属性"""
        try:
            # 构建SET子句
            set_clauses = []
            params = {"name": entity_name}
            
            for key, value in updated_props.items():
                if key != 'name':  # 名称通常不允许修改
                    param_key = f"new_{key}"
                    set_clauses.append(f"n.{key} = ${param_key}")
                    params[param_key] = value
            
            if not set_clauses:
                return True
            
            query = f"""
            MATCH (n:{entity_type} {{name: $name}})
            SET {', '.join(set_clauses)}
            RETURN n
            """
            
            results = self.db.query(query, params)
            return len(results) > 0
            
        except Exception as e:
            logger.error(f"更新实体失败: {str(e)}")
            return False
    
    def _create_relationship(self, source_name: str, source_type: str,
                           target_name: str, target_type: str,
                           relationship_type: str, direction: str) -> bool:
        """创建关系"""
        try:
            if direction == "outgoing":
                query = f"""
                MATCH (source:{source_type} {{name: $source_name}})
                MATCH (target:{target_type} {{name: $target_name}})
                CREATE (source)-[r:`{relationship_type}`]->(target)
                RETURN r
                """
            else:
                query = f"""
                MATCH (source:{source_type} {{name: $source_name}})
                MATCH (target:{target_type} {{name: $target_name}})
                CREATE (target)-[r:`{relationship_type}`]->(source)
                RETURN r
                """
            
            results = self.db.query(query, {
                "source_name": source_name,
                "target_name": target_name
            })
            
            return len(results) > 0
            
        except Exception as e:
            logger.error(f"创建关系失败: {str(e)}")
            return False
    
    def _delete_relationship(self, entity_name: str, entity_type: str, 
                           relationship: Dict) -> bool:
        """删除关系"""
        try:
            query = f"""
            MATCH (n:{entity_type} {{name: $entity_name}})-[r:`{relationship['relationship_type']}`]-(related)
            WHERE related.name = $related_name
            DELETE r
            """
            
            self.db.query(query, {
                "entity_name": entity_name,
                "related_name": relationship['related_name']
            })
            
            return True
            
        except Exception as e:
            logger.error(f"删除关系失败: {str(e)}")
            return False
    
    def _update_relationship(self, entity_name: str, entity_type: str,
                           old_relationship: Dict, new_rel_type: str) -> bool:
        """更新关系"""
        try:
            # 删除旧关系
            if self._delete_relationship(entity_name, entity_type, old_relationship):
                # 创建新关系
                return self._create_relationship(
                    entity_name, entity_type,
                    old_relationship['related_name'], old_relationship['related_type'],
                    new_rel_type, old_relationship['direction']
                )
            return False
            
        except Exception as e:
            logger.error(f"更新关系失败: {str(e)}")
            return False
    
    def _get_entities_by_type(self, entity_type: str, with_details: bool = False) -> List:
        """获取指定类型的实体列表"""
        try:
            if with_details:
                query = f"MATCH (n:{entity_type}) RETURN n.name as name, n.description as description"
                results = self.db.query(query)
                return [{"name": r["name"], "description": r.get("description", "")} for r in results]
            else:
                query = f"MATCH (n:{entity_type}) RETURN n.name as name ORDER BY n.name"
                results = self.db.query(query)
                return [r["name"] for r in results]
                
        except Exception as e:
            logger.error(f"获取实体列表失败: {str(e)}")
            return []
    
    def _display_relationship_stats(self, entity_name: str, entity_type: str):
        """显示关系统计"""
        try:
            stats_query = f"""
            MATCH (n:{entity_type} {{name: $name}})
            OPTIONAL MATCH (n)-[r]-()
            RETURN count(r) as total_relationships,
                   count(DISTINCT type(r)) as relationship_types
            """
            
            results = self.db.query(stats_query, {"name": entity_name})
            
            if results:
                stats = results[0]
                st.write("**关系统计:**")
                st.write(f"- 总关系数: {stats['total_relationships']}")
                st.write(f"- 关系类型数: {stats['relationship_types']}")
                
        except Exception as e:
            logger.error(f"获取关系统计失败: {str(e)}")
    
    def _get_type_display_name(self, entity_type: str) -> str:
        """获取类型显示名称"""
        type_names = {
            "company": "公司",
            "industry": "行业",
            "product": "产品"
        }
        return type_names.get(entity_type, entity_type)
    
    def _batch_add_tags(self, entity_type: str, df: pd.DataFrame):
        """批量添加标签"""
        # 这里可以实现批量添加标签的逻辑
        st.info("批量添加标签功能开发中...")
    
    def _batch_update_descriptions(self, entity_type: str, df: pd.DataFrame):
        """批量更新描述"""
        # 这里可以实现批量更新描述的逻辑
        st.info("批量更新描述功能开发中...")
    
    def _batch_delete_entities(self, entity_type: str, df: pd.DataFrame):
        """批量删除实体"""
        # 这里可以实现批量删除的逻辑
        st.warning("批量删除功能需要谨慎使用，暂未开放")