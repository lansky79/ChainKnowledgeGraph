"""
鐭ヨ瘑鍥捐氨楂樼骇鍙鍖栭〉闈?
"""
import streamlit as st
import streamlit_echarts as st_echarts
import pandas as pd
import numpy as np
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import logging
import traceback
import json
from datetime import datetime

# 瀵煎叆鑷畾涔夋ā鍧?
from utils.db_connector import Neo4jConnector
from utils.data_processor import process_neo4j_results, get_entity_options
from utils.logger import setup_logger
from visualizers.network_viz import display_network, create_echarts_graph

# 璁剧疆鏃ュ織
logger = setup_logger("KG_Advanced_Viz")

# 椤甸潰閰嶇疆
st.set_page_config(
    page_title="鐭ヨ瘑鍥捐氨楂樼骇鍙鍖?,
    layout="wide",
    initial_sidebar_state="expanded"
)

# 鑷畾涔塁SS锛屼娇鐣岄潰鏇寸揣鍑?
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3, h4, h5, h6 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 30px;
        padding: 5px 10px;
    }
</style>
""", unsafe_allow_html=True)

# 杈呭姪鍑芥暟锛氱洿鎺ユ覆鏌揈Charts HTML
def render_echarts_html(options, height="700px"):
    """浣跨敤HTML鐩存帴娓叉煋ECharts鍥捐〃"""
    try:
        # 纭繚鎵€鏈夋暟鍊煎瓧娈甸兘鏄暟瀛楃被鍨?
        def ensure_numeric(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ["symbolSize", "value", "category"]:
                        if isinstance(v, str) and v.isdigit():
                            obj[k] = int(v)
                    else:
                        ensure_numeric(v)
            elif isinstance(obj, list):
                for item in obj:
                    ensure_numeric(item)
            return obj
        
        # 澶勭悊鏁版嵁绫诲瀷
        options = ensure_numeric(options)
        
        # 杞崲涓篔SON瀛楃涓?
        options_str = json.dumps(options, ensure_ascii=False)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body>
            <div id="chart-container" style="width:100%; height:{height};"></div>
            <script>
                var chartDom = document.getElementById('chart-container');
                var myChart = echarts.init(chartDom);
                var options = {options_str};
                
                try {{
                    myChart.setOption(options);
                    
                    // 鑷€傚簲澶у皬
                    window.addEventListener('resize', function() {{
                        myChart.resize();
                    }});
                }} catch(e) {{
                    console.error("ECharts閿欒:", e);
                    document.getElementById('chart-container').innerHTML = 
                        '<div style="color:red;padding:20px;">鍥捐〃娓叉煋閿欒: ' + e.message + '</div>';
                }}
            </script>
        </body>
        </html>
        """
        
        components.html(html, height=height)
    except Exception as e:
        st.error(f"鍥捐〃娓叉煋閿欒: {str(e)}")
        st.code(json.dumps(options, indent=2, ensure_ascii=False), language="json")

# 鍒濆鍖栨暟鎹簱杩炴帴
@st.cache_resource
def get_db_connector():
    """鑾峰彇鏁版嵁搴撹繛鎺ュ櫒锛堢紦瀛樿祫婧愶級"""
    return Neo4jConnector()

db = get_db_connector()

# 椤甸潰鏍囬
st.title("鐭ヨ瘑鍥捐氨楂樼骇鍙鍖?)

# 鍒涘缓渚ц竟鏍?
st.sidebar.header("鏌ヨ閫夐」")

# 瀹炰綋绫诲瀷閫夋嫨
entity_type_options = {
    "company": "鍏徃",
    "industry": "琛屼笟",
    "product": "浜у搧"
}

entity_type = st.sidebar.selectbox(
    "閫夋嫨瀹炰綋绫诲瀷",
    list(entity_type_options.keys()),
    format_func=lambda x: entity_type_options.get(x, x)
)

# 鎼滅储妗?
search_query = st.sidebar.text_input("鎼滅储瀹炰綋", placeholder="杈撳叆瀹炰綋鍚嶇О")

# 鑾峰彇瀹炰綋鍒楄〃
@st.cache_data(ttl=300)
def get_entities_cached(entity_type, search_term=""):
    """缂撳瓨瀹炰綋鍒楄〃鏌ヨ缁撴灉"""
    return get_entity_options(db, entity_type, search_term)

@st.cache_data(ttl=300)
def get_related_industries(industry_name):
    """鑾峰彇涓庢寚瀹氳涓氱浉鍏崇殑鍏朵粬琛屼笟"""
    query = """
    MATCH (i:industry {name: $name})
    OPTIONAL MATCH (i)-[r]-(related:industry)
    RETURN collect(distinct related) as related_industries
    """
    results = db.query(query, {"name": industry_name})
    if results and "related_industries" in results[0]:
        return results[0]["related_industries"]
    return []

if search_query:
    entities = get_entities_cached(entity_type, search_query)
    if entities:
        selected_entity = st.sidebar.selectbox("閫夋嫨瀹炰綋", entities)
    else:
        st.sidebar.warning(f"鏈壘鍒板寘鍚?'{search_query}' 鐨剓entity_type_options.get(entity_type)}瀹炰綋")
        selected_entity = None
else:
    entities = get_entities_cached(entity_type)
    selected_entity = st.sidebar.selectbox("閫夋嫨瀹炰綋", entities) if entities else None

# 娣卞害閫夋嫨
depth = st.sidebar.slider("鍏崇郴娣卞害", 1, 3, 1)

# 鍒涘缓閫夐」鍗?
tab1, tab2, tab3, tab4 = st.tabs(["缃戠粶鍥?, "灞傜骇鏍?, "鍏崇郴鐭╅樀", "浜т笟閾?])

# 鍦ㄦ瘡涓€夐」鍗′腑娣诲姞鍒濆鍐呭
with tab1:
    st.info("鐐瑰嚮宸︿晶鐨?鐢熸垚鍙鍖?鎸夐挳锛屾煡鐪嬬綉缁滃浘鍙鍖?)
    
with tab2:
    st.info("鐐瑰嚮宸︿晶鐨?鐢熸垚鍙鍖?鎸夐挳锛屾煡鐪嬪眰绾ф爲鍙鍖栵紙浠呮敮鎸佽涓氱被鍨嬶級")
    
with tab3:
    st.info("鐐瑰嚮宸︿晶鐨?鐢熸垚鍙鍖?鎸夐挳锛屾煡鐪嬪叧绯荤煩闃靛彲瑙嗗寲")
    
with tab4:
    st.info("鐐瑰嚮宸︿晶鐨?鐢熸垚鍙鍖?鎸夐挳锛屾煡鐪嬩骇涓氶摼鍙鍖栵紙浠呮敮鎸佽涓氱被鍨嬶級")

# 鍙鍖栨寜閽?
if selected_entity and st.sidebar.button("鐢熸垚鍙鍖?, use_container_width=True):
    # 鏄剧ず鏍囬
    st.header(f"{selected_entity} 鐭ヨ瘑鍥捐氨")
    
    with st.spinner("姝ｅ湪鐢熸垚鐭ヨ瘑鍥捐氨..."):
        try:
            # 鏋勫缓鏌ヨ
            if entity_type == "industry":
                query = f"""
                MATCH (i:{entity_type} {{name: $name}})
                OPTIONAL MATCH (c:company)-[r1:鎵€灞炶涓歖->(i)
                OPTIONAL MATCH (c)-[r2:涓昏惀浜у搧]->(p:product)
                OPTIONAL MATCH (i)-[r3]-(related:industry)
                RETURN i, collect(distinct c) as companies, 
                       collect(distinct p) as products,
                       collect(distinct related) as related_industries
                """
            elif entity_type == "company":
                query = f"""
                MATCH (c:{entity_type} {{name: $name}})
                OPTIONAL MATCH (c)-[r1:鎵€灞炶涓歖->(i:industry)
                OPTIONAL MATCH (c)-[r2:涓昏惀浜у搧]->(p:product)
                RETURN c, collect(distinct i) as industries, collect(distinct p) as products
                """
            else:  # product
                query = f"""
                MATCH (p:{entity_type} {{name: $name}})
                OPTIONAL MATCH (c:company)-[r1:涓昏惀浜у搧]->(p)
                OPTIONAL MATCH (p)-[r2:涓婃父鏉愭枡]->(up:product)
                RETURN p, collect(distinct c) as companies, collect(distinct up) as upstream_products
                """
            
            # 鎵ц鏌ヨ
            logger.info(f"鎵ц鏌ヨ: {query}")
            results = db.query(query, {"name": selected_entity})
            
            if results:
                # 鍒涘缓鑺傜偣鍜岃竟鐨勫垪琛?
                nodes = []
                edges = []
                node_ids = {}
                
                try:
                    # 澶勭悊涓績瀹炰綋
                    if entity_type == "industry":
                        if "i" in results[0]:
                            industry = results[0]["i"]
                            industry_id = industry.identity
                            nodes.append({
                                "id": industry_id,
                                "label": industry["name"],
                                "group": 0  # 琛屼笟
                            })
                            node_ids[industry_id] = True
                        
                        # 澶勭悊鐩稿叧琛屼笟
                        related_industries = results[0].get("related_industries", [])
                        for rel_industry in related_industries:
                            if rel_industry and rel_industry.identity != industry_id:  # 閬垮厤閲嶅娣诲姞涓績琛屼笟
                                rel_industry_id = rel_industry.identity
                                if rel_industry_id not in node_ids:
                                    nodes.append({
                                        "id": rel_industry_id,
                                        "label": rel_industry["name"],
                                        "group": 0  # 琛屼笟
                                    })
                                    node_ids[rel_industry_id] = True
                                    
                                    # 娣诲姞琛屼笟闂村叧绯昏竟
                                    edges.append({
                                        "from": industry_id,
                                        "to": rel_industry_id,
                                        "label": "鐩稿叧琛屼笟"
                                    })
                    
                        # 澶勭悊鍏徃
                        companies = results[0].get("companies", [])
                        for company in companies:
                            if company:
                                company_id = company.identity
                                if company_id not in node_ids:
                                    nodes.append({
                                        "id": company_id,
                                        "label": company["name"],
                                        "group": 1  # 鍏徃
                                    })
                                    node_ids[company_id] = True
                                    
                                    # 娣诲姞鍏徃->琛屼笟鐨勮竟
                                    edges.append({
                                        "from": company_id,
                                        "to": industry_id,
                                        "label": "鎵€灞炶涓?
                                    })
                        
                        # 澶勭悊浜у搧
                        products = results[0].get("products", [])
                        for product in products:
                            if product:
                                product_id = product.identity
                                if product_id not in node_ids:
                                    nodes.append({
                                        "id": product_id,
                                        "label": product["name"],
                                        "group": 2  # 浜у搧
                                    })
                                    node_ids[product_id] = True
                                
                                # 鎵惧埌鍏宠仈鐨勫叕鍙?
                                for company in companies:
                                    if company:
                                        company_id = company.identity
                                        # 娣诲姞鍏徃->浜у搧鐨勮竟
                                        edges.append({
                                            "from": company_id,
                                            "to": product_id,
                                            "label": "涓昏惀浜у搧"
                                        })
                    
                    elif entity_type == "company":
                        if "c" in results[0]:
                            company = results[0]["c"]
                            company_id = company.identity
                            nodes.append({
                                "id": company_id,
                                "label": company["name"],
                                "group": 1  # 鍏徃
                            })
                            node_ids[company_id] = True
                        
                        # 澶勭悊琛屼笟
                        industries = results[0].get("industries", [])
                        for industry in industries:
                            if industry:
                                industry_id = industry.identity
                                if industry_id not in node_ids:
                                    nodes.append({
                                        "id": industry_id,
                                        "label": industry["name"],
                                        "group": 0  # 琛屼笟
                                    })
                                    node_ids[industry_id] = True
                                    
                                    # 娣诲姞鍏徃->琛屼笟鐨勮竟
                                    edges.append({
                                        "from": company_id,
                                        "to": industry_id,
                                        "label": "鎵€灞炶涓?
                                    })
                        
                        # 澶勭悊浜у搧
                        products = results[0].get("products", [])
                        for product in products:
                            if product:
                                product_id = product.identity
                                if product_id not in node_ids:
                                    nodes.append({
                                        "id": product_id,
                                        "label": product["name"],
                                        "group": 2  # 浜у搧
                                    })
                                    node_ids[product_id] = True
                                    
                                    # 娣诲姞鍏徃->浜у搧鐨勮竟
                                    edges.append({
                                        "from": company_id,
                                        "to": product_id,
                                        "label": "涓昏惀浜у搧"
                                    })
                    
                    else:  # product
                        if "p" in results[0]:
                            product = results[0]["p"]
                            product_id = product.identity
                            nodes.append({
                                "id": product_id,
                                "label": product["name"],
                                "group": 2  # 浜у搧
                            })
                            node_ids[product_id] = True
                        
                        # 澶勭悊鍏徃
                        companies = results[0].get("companies", [])
                        for company in companies:
                            if company:
                                company_id = company.identity
                                if company_id not in node_ids:
                                    nodes.append({
                                        "id": company_id,
                                        "label": company["name"],
                                        "group": 1  # 鍏徃
                                    })
                                    node_ids[company_id] = True
                                    
                                    # 娣诲姞鍏徃->浜у搧鐨勮竟
                                    edges.append({
                                        "from": company_id,
                                        "to": product_id,
                                        "label": "涓昏惀浜у搧"
                                    })
                        
                        # 澶勭悊涓婃父浜у搧
                        upstream_products = results[0].get("upstream_products", [])
                        for upstream in upstream_products:
                            if upstream:
                                upstream_id = upstream.identity
                                if upstream_id not in node_ids:
                                    nodes.append({
                                        "id": upstream_id,
                                        "label": upstream["name"],
                                        "group": 2  # 浜у搧
                                    })
                                    node_ids[upstream_id] = True
                                    
                                    # 娣诲姞浜у搧->涓婃父浜у搧鐨勮竟
                                    edges.append({
                                        "from": product_id,
                                        "to": upstream_id,
                                        "label": "涓婃父鏉愭枡"
                                    })
                
                except Exception as e:
                    logger.error(f"澶勭悊鏌ヨ缁撴灉鏃跺嚭閿? {str(e)}")
                    logger.error(traceback.format_exc())
                    st.error(f"澶勭悊鏌ヨ缁撴灉鏃跺嚭閿? {str(e)}")
                
                # 鏄剧ず鑺傜偣鍜岃竟鐨勬暟閲?
                st.info(f"鎵惧埌 {len(nodes)} 涓妭鐐瑰拰 {len(edges)} 鏉″叧绯?)
                
                # 鍦ㄤ笉鍚岄€夐」鍗′腑鏄剧ず涓嶅悓鐨勫彲瑙嗗寲
                if nodes and edges:
                    # 缃戠粶鍥鹃€夐」鍗?
                    with tab1:
                        if display_network(nodes, edges, f"{selected_entity} 鐭ヨ瘑鍥捐氨"):
                            st.success(f"鎴愬姛鐢熸垚 {selected_entity} 鐨勭綉缁滃浘")
                        else:
                            st.error("鐢熸垚缃戠粶鍥惧け璐?)
                    
                    # 灞傜骇鏍戦€夐」鍗?
                    with tab2:
                        try:
                            # 鏋勫缓灞傜骇鏍戞暟鎹?
                            if entity_type == "industry":
                                # 鏋勫缓灞傜骇鏍戞煡璇?
                                tree_query = f"""
                                MATCH (i:industry {{name: $name}})
                                OPTIONAL MATCH (sub:industry)-[:涓婄骇琛屼笟]->(i)
                                OPTIONAL MATCH (c:company)-[:鎵€灞炶涓歖->(i)
                                OPTIONAL MATCH (c2:company)-[:鎵€灞炶涓歖->(sub)
                                RETURN i, collect(distinct sub) as sub_industries, 
                                       collect(distinct c) as direct_companies,
                                       collect(distinct c2) as sub_companies
                                """
                                
                                tree_results = db.query(tree_query, {"name": selected_entity})
                                
                                if tree_results:
                                    # 鑾峰彇鏌ヨ缁撴灉涓殑鏁版嵁
                                    sub_industries = tree_results[0].get("sub_industries", [])
                                    direct_companies = tree_results[0].get("direct_companies", [])
                                    sub_companies = tree_results[0].get("sub_companies", [])
                                    
                                    # 浣跨敤Streamlit鍘熺敓缁勪欢鏋勫缓灞傜骇鏍?
                                    st.subheader("琛屼笟灞傜骇缁撴瀯")
                                    
                                    # 鏋勫缓绠€鍗曠殑鏍戝舰缁撴瀯
                                    tree_data = {}
                                    
                                    # 娣诲姞鏍硅妭鐐癸紙閫変腑鐨勮涓氾級
                                    tree_data[selected_entity] = {"瀛愯涓?: {}, "鐩村睘鍏徃": []}
                                    
                                    # 娣诲姞瀛愯涓?
                                    for sub in sub_industries:
                                        if sub and sub["name"] != selected_entity:
                                            tree_data[selected_entity]["瀛愯涓?][sub["name"]] = {"鐩村睘鍏徃": []}
                                    
                                    # 娣诲姞鐩村睘鍏徃
                                    for company in direct_companies:
                                        if company:
                                            tree_data[selected_entity]["鐩村睘鍏徃"].append(company["name"])
                                    
                                    # 娣诲姞瀛愯涓氱殑鍏徃
                                    for company in sub_companies:
                                        if company:
                                            # 鏌ユ壘璇ュ叕鍙稿睘浜庡摢涓瓙琛屼笟
                                            for sub in sub_industries:
                                                if sub:
                                                    rel_query = """
                                                    MATCH (c:company {name: $company_name})-[r:鎵€灞炶涓歖->(i:industry {name: $industry_name})
                                                    RETURN count(r) > 0 as has_relationship
                                                    """
                                                    rel_result = db.query(rel_query, {
                                                        "company_name": company["name"],
                                                        "industry_name": sub["name"]
                                                    })
                                                    
                                                    if rel_result and rel_result[0]["has_relationship"]:
                                                        if sub["name"] in tree_data[selected_entity]["瀛愯涓?]:
                                                            tree_data[selected_entity]["瀛愯涓?][sub["name"]]["鐩村睘鍏徃"].append(company["name"])
                                    
                                    # 鏄剧ず鏍戝舰缁撴瀯
                                    st.json(tree_data, expanded=True)
                                    
                                    # 鍒涘缓鍙鍖栬〃绀?
                                    st.subheader("灞傜骇鏍戝彲瑙嗗寲")
                                    
                                    # 浣跨敤Markdown鍒涘缓绠€鍗曠殑鏍戝舰鍥?
                                    md_tree = f"### {selected_entity}\n"
                                    
                                    # 娣诲姞瀛愯涓?
                                    if tree_data[selected_entity]["瀛愯涓?]:
                                        md_tree += "\n#### 瀛愯涓?\n"
                                        for sub_name, sub_data in tree_data[selected_entity]["瀛愯涓?].items():
                                            md_tree += f"- **{sub_name}**\n"
                                            if sub_data["鐩村睘鍏徃"]:
                                                md_tree += "  - 鐩村睘鍏徃:\n"
                                                for company in sub_data["鐩村睘鍏徃"]:
                                                    md_tree += f"    - {company}\n"
                                    
                                    # 娣诲姞鐩村睘鍏徃
                                    if tree_data[selected_entity]["鐩村睘鍏徃"]:
                                        md_tree += "\n#### 鐩村睘鍏徃:\n"
                                        for company in tree_data[selected_entity]["鐩村睘鍏徃"]:
                                            md_tree += f"- {company}\n"
                                    
                                    st.markdown(md_tree)
                                    st.success(f"鎴愬姛鐢熸垚 {selected_entity} 鐨勫眰绾ф爲")
                                else:
                                    st.warning("娌℃湁鎵惧埌灞傜骇鏍戞暟鎹?)
                            else:
                                st.info("灞傜骇鏍戝彲瑙嗗寲浠呮敮鎸佽涓氱被鍨嬬殑瀹炰綋")
                        except Exception as e:
                            st.error(f"鐢熸垚灞傜骇鏍戞椂鍑洪敊: {str(e)}")
                            logger.error(f"鐢熸垚灞傜骇鏍戞椂鍑洪敊: {str(e)}\n{traceback.format_exc()}")
                    
                    # 鍏崇郴鐭╅樀閫夐」鍗?
                    with tab3:
                        try:
                            # 鎸夊疄浣撶被鍨嬪鑺傜偣杩涜鍒嗙粍
                            node_types = {}
                            for node in nodes:
                                # 鑾峰彇鑺傜偣绫诲瀷
                                node_type = node.get("group", 0)
                                if node_type not in node_types:
                                    node_types[node_type] = []
                                node_types[node_type].append(node)
                            
                            # 鎻愪緵鐭╅樀绫诲瀷閫夋嫨
                            matrix_type_options = ["鍚岀被鍨嬪疄浣撶煩闃?, "鍏徃-浜у搧鐭╅樀"]
                            matrix_type = st.radio("閫夋嫨鐭╅樀绫诲瀷", matrix_type_options)
                            
                            if matrix_type == "鍚岀被鍨嬪疄浣撶煩闃?:
                                # 璁╃敤鎴烽€夋嫨瑕佹樉绀虹殑瀹炰綋绫诲瀷
                                type_names = {0: "琛屼笟", 1: "鍏徃", 2: "浜у搧"}
                                available_types = [type_names.get(t, f"绫诲瀷{t}") for t in node_types.keys()]
                                
                                if not available_types:
                                    st.warning("娌℃湁瓒冲鐨勮妭鐐规潵鍒涘缓鐭╅樀")
                                    st.stop()
                                
                                selected_type = st.selectbox("閫夋嫨瀹炰綋绫诲瀷", available_types)
                                
                                # 鑾峰彇閫夋嫨鐨勭被鍨嬬储寮?
                                selected_type_idx = list(type_names.values()).index(selected_type) if selected_type in type_names.values() else 0
                                
                                # 璋冭瘯淇℃伅
                                st.write(f"褰撳墠閫夋嫨鐨勭被鍨? {selected_type}锛岀储寮? {selected_type_idx}")
                                st.write(f"鍙敤鐨勮妭鐐圭被鍨? {node_types.keys()}")
                                if selected_type_idx in node_types:
                                    st.write(f"璇ョ被鍨嬭妭鐐规暟閲? {len(node_types[selected_type_idx])}")
                                
                                # 鑾峰彇璇ョ被鍨嬬殑鎵€鏈夎妭鐐?
                                if selected_type_idx not in node_types or len(node_types[selected_type_idx]) < 2:
                                    # 灏濊瘯鎵╁睍鏌ヨ鑾峰彇鏇村鐩稿叧琛屼笟鑺傜偣
                                    if selected_type == "琛屼笟" and entity_type == "industry":
                                        st.info("姝ｅ湪灏濊瘯鑾峰彇鏇村鐩稿叧琛屼笟鑺傜偣...")
                                        # 鏋勫缓鎵╁睍鏌ヨ锛岃幏鍙栫浉鍏宠涓?
                                        expand_query = f"""
                                        MATCH (i:industry {{name: $name}})
                                        OPTIONAL MATCH (i)-[r]-(related:industry)
                                        RETURN i, collect(distinct related) as related_industries
                                        """
                                        
                                        expand_results = db.query(expand_query, {"name": selected_entity})
                                        
                                        if expand_results and "related_industries" in expand_results[0]:
                                            related_industries = expand_results[0]["related_industries"]
                                            
                                            # 娣诲姞鐩稿叧琛屼笟鑺傜偣
                                            for industry in related_industries:
                                                if industry and industry.identity not in node_ids:
                                                    industry_id = industry.identity
                                                    nodes.append({
                                                        "id": industry_id,
                                                        "label": industry["name"],
                                                        "group": 0  # 琛屼笟
                                                    })
                                                    node_ids[industry_id] = True
                                            
                                            # 閲嶆柊鏋勫缓鑺傜偣绫诲瀷鍒嗙粍
                                            node_types = {}
                                            for node in nodes:
                                                node_type = node.get("group", 0)
                                                if node_type not in node_types:
                                                    node_types[node_type] = []
                                                node_types[node_type].append(node)
                                            
                                            # 閲嶆柊妫€鏌ヨ妭鐐规暟閲?
                                            if 0 in node_types and len(node_types[0]) >= 2:
                                                st.success(f"鎴愬姛鑾峰彇鍒?{len(node_types[0])} 涓涓氳妭鐐?)
                                                selected_type_idx = 0  # 琛屼笟绫诲瀷绱㈠紩
                                            else:
                                                st.warning(f"娌℃湁瓒冲鐨剓selected_type}鑺傜偣鏉ュ垱寤虹煩闃?)
                                                st.stop()
                                        else:
                                            st.warning(f"娌℃湁瓒冲鐨剓selected_type}鑺傜偣鏉ュ垱寤虹煩闃?)
                                            st.stop()
                                    else:
                                        st.warning(f"娌℃湁瓒冲鐨剓selected_type}鑺傜偣鏉ュ垱寤虹煩闃?)
                                        st.stop()
                                
                                type_nodes = node_types[selected_type_idx]
                                matrix_nodes = [node["label"] for node in type_nodes]
                                
                                # 鍒涘缓鐭╅樀
                                matrix = np.zeros((len(matrix_nodes), len(matrix_nodes)))
                                
                                # 鑺傜偣鏍囩鍒扮储寮曠殑鏄犲皠
                                node_label_to_index = {node["label"]: i for i, node in enumerate(type_nodes)}
                                
                                # 濉厖鐭╅樀
                                for edge in edges:
                                    source_node = next((node for node in nodes if node["id"] == edge["from"]), None)
                                    target_node = next((node for node in nodes if node["id"] == edge["to"]), None)
                                    
                                    # 纭繚涓や釜鑺傜偣閮芥槸鎵€閫夌被鍨?
                                    if (source_node and target_node and 
                                        source_node.get("group", 0) == selected_type_idx and 
                                        target_node.get("group", 0) == selected_type_idx):
                                        
                                        source_label = source_node["label"]
                                        target_label = target_node["label"]
                                        
                                        if source_label in node_label_to_index and target_label in node_label_to_index:
                                            source_idx = node_label_to_index[source_label]
                                            target_idx = node_label_to_index[target_label]
                                            matrix[source_idx][target_idx] = 1
                            
                            elif matrix_type == "鍏徃-浜у搧鐭╅樀":
                                # 纭繚鏈夊叕鍙稿拰浜у搧鑺傜偣
                                if 1 not in node_types or 2 not in node_types:
                                    # 灏濊瘯鎵╁睍鏌ヨ鑾峰彇鏇村鍏徃鍜屼骇鍝佽妭鐐?
                                    st.info("姝ｅ湪灏濊瘯鑾峰彇鏇村鍏徃鍜屼骇鍝佽妭鐐?..")
                                    
                                    if entity_type == "industry":
                                        # 鏋勫缓鎵╁睍鏌ヨ锛岃幏鍙栨洿澶氬叕鍙稿拰浜у搧
                                        expand_query = f"""
                                        MATCH (i:industry {{name: $name}})
                                        OPTIONAL MATCH (c:company)-[:鎵€灞炶涓歖->(i)
                                        OPTIONAL MATCH (c)-[:涓昏惀浜у搧]->(p:product)
                                        WITH i, collect(distinct c) as companies, collect(distinct p) as products
                                        UNWIND companies as company
                                        OPTIONAL MATCH (company)-[:涓昏惀浜у搧]->(other_product:product)
                                        RETURN i, companies, products, collect(distinct other_product) as other_products
                                        """
                                        
                                        expand_results = db.query(expand_query, {"name": selected_entity})
                                        
                                        if expand_results:
                                            # 娣诲姞鏇村鍏徃鍜屼骇鍝佽妭鐐?
                                            companies = expand_results[0].get("companies", [])
                                            products = expand_results[0].get("products", [])
                                            other_products = expand_results[0].get("other_products", [])
                                            
                                            # 娣诲姞鍏徃鑺傜偣
                                            for company in companies:
                                                if company and company.identity not in node_ids:
                                                    company_id = company.identity
                                                    nodes.append({
                                                        "id": company_id,
                                                        "label": company["name"],
                                                        "group": 1  # 鍏徃
                                                    })
                                                    node_ids[company_id] = True
                                            
                                            # 娣诲姞浜у搧鑺傜偣
                                            all_products = list(products) + list(other_products)
                                            for product in all_products:
                                                if product and product.identity not in node_ids:
                                                    product_id = product.identity
                                                    nodes.append({
                                                        "id": product_id,
                                                        "label": product["name"],
                                                        "group": 2  # 浜у搧
                                                    })
                                                    node_ids[product_id] = True
                                            
                                            # 閲嶆柊鏋勫缓鑺傜偣绫诲瀷鍒嗙粍
                                            node_types = {}
                                            for node in nodes:
                                                node_type = node.get("group", 0)
                                                if node_type not in node_types:
                                                    node_types[node_type] = []
                                                node_types[node_type].append(node)
                                            
                                            # 閲嶆柊妫€鏌ヨ妭鐐规暟閲?
                                            if 1 in node_types and 2 in node_types:
                                                st.success(f"鎴愬姛鑾峰彇鍒?{len(node_types[1])} 涓叕鍙歌妭鐐瑰拰 {len(node_types[2])} 涓骇鍝佽妭鐐?)
                                            else:
                                                st.warning("娌℃湁瓒冲鐨勫叕鍙稿拰浜у搧鑺傜偣鏉ュ垱寤虹煩闃?)
                                                st.stop()
                                        else:
                                            st.warning("娌℃湁瓒冲鐨勫叕鍙稿拰浜у搧鑺傜偣鏉ュ垱寤虹煩闃?)
                                            st.stop()
                                    else:
                                        st.warning("娌℃湁瓒冲鐨勫叕鍙稿拰浜у搧鑺傜偣鏉ュ垱寤虹煩闃?)
                                        st.stop()
                                
                                # 鑾峰彇鍏徃鍜屼骇鍝佽妭鐐?
                                company_nodes = node_types[1]
                                product_nodes = node_types[2]
                                
                                # 濡傛灉鏄涓氱被鍨嬶紝纭繚鎴戜滑鏈夎冻澶熺殑鍏徃鍜屼骇鍝佹暟鎹?
                                if entity_type == "industry" and (len(company_nodes) < 2 or len(product_nodes) < 2):
                                    st.info(f"姝ｅ湪涓?{selected_entity} 琛屼笟鑾峰彇鏇村鍏徃鍜屼骇鍝佹暟鎹?..")
                                    
                                    # 鐩存帴浠庢暟鎹簱鏌ヨ璇ヨ涓氫笅鐨勬墍鏈夊叕鍙稿拰浜у搧
                                    extended_query = """
                                    MATCH (i:industry {name: $name})
                                    MATCH (c:company)-[:鎵€灞炶涓歖->(i)
                                    OPTIONAL MATCH (c)-[:涓昏惀浜у搧]->(p:product)
                                    RETURN collect(distinct c) as companies, collect(distinct p) as products
                                    """
                                    
                                    extended_results = db.query(extended_query, {"name": selected_entity})
                                    
                                    if extended_results:
                                        # 娣诲姞鍏徃鑺傜偣
                                        companies = extended_results[0].get("companies", [])
                                        for company in companies:
                                            if company and company.identity not in node_ids:
                                                company_id = company.identity
                                                nodes.append({
                                                    "id": company_id,
                                                    "label": company["name"],
                                                    "group": 1  # 鍏徃
                                                })
                                                node_ids[company_id] = True
                                        
                                        # 娣诲姞浜у搧鑺傜偣
                                        products = extended_results[0].get("products", [])
                                        for product in products:
                                            if product and product.identity not in node_ids:
                                                product_id = product.identity
                                                nodes.append({
                                                    "id": product_id,
                                                    "label": product["name"],
                                                    "group": 2  # 浜у搧
                                                })
                                                node_ids[product_id] = True
                                        
                                        # 閲嶆柊鏋勫缓鑺傜偣绫诲瀷鍒嗙粍
                                        node_types = {}
                                        for node in nodes:
                                            node_type = node.get("group", 0)
                                            if node_type not in node_types:
                                                node_types[node_type] = []
                                            node_types[node_type].append(node)
                                        
                                        # 鏇存柊鍏徃鍜屼骇鍝佽妭鐐瑰垪琛?
                                        if 1 in node_types:
                                            company_nodes = node_types[1]
                                        if 2 in node_types:
                                            product_nodes = node_types[2]
                                            
                                        st.success(f"鎴愬姛鑾峰彇鍒?{len(company_nodes)} 涓叕鍙歌妭鐐瑰拰 {len(product_nodes)} 涓骇鍝佽妭鐐?)
                                
                                # 鍒涘缓鐭╅樀
                                matrix = np.zeros((len(company_nodes), len(product_nodes)))
                                
                                # 鍏徃鍜屼骇鍝佹爣绛惧埌绱㈠紩鐨勬槧灏?
                                company_label_to_index = {node["label"]: i for i, node in enumerate(company_nodes)}
                                product_label_to_index = {node["label"]: i for i, node in enumerate(product_nodes)}
                                
                                # 濉厖鐭╅樀
                                # 璋冭瘯淇℃伅
                                st.write(f"鍏徃鑺傜偣鏁? {len(company_nodes)}, 浜у搧鑺傜偣鏁? {len(product_nodes)}")
                                st.write(f"杈规暟: {len(edges)}")
                                
                                # 鐩存帴鏌ヨ鏁版嵁搴撹幏鍙栧叕鍙?浜у搧鍏崇郴
                                if entity_type == "industry":
                                    # 鑾峰彇璇ヨ涓氫笅鐨勫叕鍙?浜у搧鍏崇郴
                                    relation_query = """
                                    MATCH (i:industry {name: $name})
                                    MATCH (c:company)-[:鎵€灞炶涓歖->(i)
                                    MATCH (c)-[:涓昏惀浜у搧]->(p:product)
                                    RETURN c.name as company, p.name as product
                                    UNION
                                    MATCH (i:industry {name: $name})
                                    MATCH (c:company)-[:鎵€灞炶涓歖->(i)
                                    MATCH (c)-[r]->(p:product)
                                    WHERE type(r) IN ['鐢熶骇', '閿€鍞?, '鐮斿彂']
                                    RETURN c.name as company, p.name as product
                                    """
                                    relation_results = db.query(relation_query, {"name": selected_entity})
                                    
                                    # 鏄剧ず鏌ヨ鍒扮殑鍏崇郴鏁?
                                    st.write(f"浠庢暟鎹簱鏌ヨ鍒?{len(relation_results)} 鏉″叕鍙?浜у搧鍏崇郴")
                                    
                                    # 浣跨敤杩欎簺鍏崇郴濉厖鐭╅樀
                                    for relation in relation_results:
                                        company_name = relation["company"]
                                        product_name = relation["product"]
                                        
                                        # 纭繚鍏徃鍜屼骇鍝佸湪鎴戜滑鐨勮妭鐐瑰垪琛ㄤ腑
                                        company_found = False
                                        for i, company_node in enumerate(company_nodes):
                                            if company_node["label"] == company_name:
                                                company_idx = i
                                                company_found = True
                                                break
                                        
                                        product_found = False
                                        for j, product_node in enumerate(product_nodes):
                                            if product_node["label"] == product_name:
                                                product_idx = j
                                                product_found = True
                                                break
                                        
                                        # 濡傛灉鎵惧埌浜嗗叕鍙稿拰浜у搧锛屽～鍏呯煩闃?
                                        if company_found and product_found:
                                            matrix[company_idx][product_idx] = 1
                                else:
                                    # 浣跨敤杈逛俊鎭～鍏呯煩闃?
                                    for edge in edges:
                                        source_node = next((node for node in nodes if node["id"] == edge["from"]), None)
                                        target_node = next((node for node in nodes if node["id"] == edge["to"]), None)
                                        
                                        if source_node and target_node:
                                            source_group = source_node.get("group", 0)
                                            target_group = target_node.get("group", 0)
                                            
                                            # 鍏徃 -> 浜у搧 鍏崇郴
                                            if source_group == 1 and target_group == 2:
                                                source_label = source_node["label"]
                                                target_label = target_node["label"]
                                                
                                                company_idx = -1
                                                for i, company_node in enumerate(company_nodes):
                                                    if company_node["label"] == source_label:
                                                        company_idx = i
                                                        break
                                                
                                                product_idx = -1
                                                for j, product_node in enumerate(product_nodes):
                                                    if product_node["label"] == target_label:
                                                        product_idx = j
                                                        break
                                                
                                                if company_idx >= 0 and product_idx >= 0:
                                                    matrix[company_idx][product_idx] = 1
                                            
                                            # 浜у搧 -> 鍏徃 鍏崇郴
                                            elif source_group == 2 and target_group == 1:
                                                source_label = source_node["label"]
                                                target_label = target_node["label"]
                                                
                                                company_idx = -1
                                                for i, company_node in enumerate(company_nodes):
                                                    if company_node["label"] == target_label:
                                                        company_idx = i
                                                        break
                                                
                                                product_idx = -1
                                                for j, product_node in enumerate(product_nodes):
                                                    if product_node["label"] == source_label:
                                                        product_idx = j
                                                        break
                                                
                                                if company_idx >= 0 and product_idx >= 0:
                                                    matrix[company_idx][product_idx] = 1
                                
                                # 璁剧疆鐭╅樀鑺傜偣鏍囩
                                matrix_nodes_x = [node["label"] for node in product_nodes]
                                matrix_nodes_y = [node["label"] for node in company_nodes]
                            
                            # 鏄剧ず鐭╅樀鍥?
                            import matplotlib.pyplot as plt
                            import matplotlib
                            
                            # 璁剧疆涓枃瀛椾綋鏀寔
                            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
                            plt.rcParams['axes.unicode_minus'] = False
                            
                            # 鍒涘缓鍥捐〃
                            fig, ax = plt.subplots(figsize=(12, 10))
                            
                            if matrix_type == "鍚岀被鍨嬪疄浣撶煩闃?:
                                im = ax.imshow(matrix, cmap="Blues")
                                
                                # 璁剧疆鍧愭爣杞存爣绛?
                                ax.set_xticks(np.arange(len(matrix_nodes)))
                                ax.set_yticks(np.arange(len(matrix_nodes)))
                                ax.set_xticklabels(matrix_nodes, fontsize=10)
                                ax.set_yticklabels(matrix_nodes, fontsize=10)
                                
                                # 娣诲姞鏍囬
                                ax.set_title(f"{selected_entity} {selected_type}鍏崇郴鐭╅樀", fontsize=14)
                                
                                # 娣诲姞缃戞牸绾?
                                ax.set_xticks(np.arange(-.5, len(matrix_nodes), 1), minor=True)
                                ax.set_yticks(np.arange(-.5, len(matrix_nodes), 1), minor=True)
                                
                                # 鍦ㄧ煩闃典腑娣诲姞鏂囨湰鏍囩
                                for i in range(len(matrix_nodes)):
                                    for j in range(len(matrix_nodes)):
                                        if matrix[i, j] > 0:
                                            ax.text(j, i, "鈼?, ha="center", va="center", color="white", fontsize=12)
                            
                            elif matrix_type == "鍏徃-浜у搧鐭╅樀":
                                im = ax.imshow(matrix, cmap="Blues")
                                
                                # 璁剧疆鍧愭爣杞存爣绛?
                                ax.set_xticks(np.arange(len(matrix_nodes_x)))
                                ax.set_yticks(np.arange(len(matrix_nodes_y)))
                                ax.set_xticklabels(matrix_nodes_x, fontsize=10)
                                ax.set_yticklabels(matrix_nodes_y, fontsize=10)
                                
                                # 娣诲姞鏍囬
                                ax.set_title(f"{selected_entity} 鍏徃-浜у搧鍏崇郴鐭╅樀", fontsize=14)
                                
                                # 娣诲姞缃戞牸绾?
                                ax.set_xticks(np.arange(-.5, len(matrix_nodes_x), 1), minor=True)
                                ax.set_yticks(np.arange(-.5, len(matrix_nodes_y), 1), minor=True)
                                
                                # 鍦ㄧ煩闃典腑娣诲姞鏂囨湰鏍囩
                                for i in range(len(matrix_nodes_y)):
                                    for j in range(len(matrix_nodes_x)):
                                        if matrix[i, j] > 0:
                                            ax.text(j, i, "鈼?, ha="center", va="center", color="white", fontsize=12)
                            
                            # 鏃嬭浆X杞存爣绛?
                            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
                            
                            # 娣诲姞缃戞牸绾?
                            ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
                            
                            # 璋冩暣甯冨眬
                            plt.tight_layout()
                            
                            # 鏄剧ず鍥惧舰
                            st.pyplot(fig)
                            st.success(f"鎴愬姛鐢熸垚 {selected_entity} 鐨勫叧绯荤煩闃?)
                        except Exception as e:
                            st.error(f"鐢熸垚鍏崇郴鐭╅樀鏃跺嚭閿? {str(e)}")
                            logger.error(f"鐢熸垚鍏崇郴鐭╅樀鏃跺嚭閿? {str(e)}\n{traceback.format_exc()}")
                    
                    # 浜т笟閾鹃€夐」鍗?
                    with tab4:
                        try:
                            # 鏋勫缓浜т笟閾炬暟鎹?
                            if entity_type == "industry":
                                # 鏋勫缓浜т笟閾炬煡璇?
                                chain_query = f"""
                                MATCH (i:industry {{name: $name}})
                                OPTIONAL MATCH (c:company)-[:鎵€灞炶涓歖->(i)
                                OPTIONAL MATCH (c)-[:涓昏惀浜у搧]->(p:product)
                                OPTIONAL MATCH (p)-[:涓婃父鏉愭枡]->(up:product)
                                RETURN i, collect(distinct c) as companies, 
                                       collect(distinct p) as products,
                                       collect(distinct up) as upstream_products
                                """
                                
                                chain_results = db.query(chain_query, {"name": selected_entity})
                                
                                if chain_results:
                                    # 浣跨敤Pyvis搴撳垱寤轰骇涓氶摼鍙鍖?
                                    st.subheader("浜т笟閾惧彲瑙嗗寲")
                                    
                                    # 鍒涘缓Pyvis缃戠粶鍥?
                                    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="black")
                                    
                                    # 娣诲姞鑺傜偣
                                    # 娣诲姞琛屼笟鑺傜偣
                                    net.add_node(selected_entity, label=selected_entity, title=selected_entity, 
                                                color="#5470c6", size=30, group=1)
                                    
                                    # 娣诲姞鍏徃鑺傜偣
                                    companies = chain_results[0].get("companies", [])
                                    for company in companies:
                                        if company:
                                            company_name = company["name"]
                                            net.add_node(company_name, label=company_name, title=company_name,
                                                        color="#91cc75", size=25, group=2)
                                            net.add_edge(company_name, selected_entity, title="鎵€灞炶涓?)
                                    
                                    # 娣诲姞浜у搧鑺傜偣
                                    products = chain_results[0].get("products", [])
                                    for product in products:
                                        if product:
                                            product_name = product["name"]
                                            net.add_node(product_name, label=product_name, title=product_name,
                                                        color="#fac858", size=20, group=3)
                                            
                                            # 鎵惧埌鍏宠仈鐨勫叕鍙?
                                            for company in companies:
                                                if company:
                                                    # 鏌ヨ鍏徃鍜屼骇鍝佺殑鍏崇郴
                                                    rel_query = """
                                                    MATCH (c:company {name: $company_name})-[r:涓昏惀浜у搧]->(p:product {name: $product_name})
                                                    RETURN count(r) > 0 as has_relationship
                                                    """
                                                    rel_result = db.query(rel_query, {
                                                        "company_name": company["name"],
                                                        "product_name": product_name
                                                    })
                                                    
                                                    if rel_result and rel_result[0]["has_relationship"]:
                                                        net.add_edge(company["name"], product_name, title="涓昏惀浜у搧")
                                    
                                    # 娣诲姞涓婃父浜у搧鑺傜偣
                                    upstream_products = chain_results[0].get("upstream_products", [])
                                    for upstream in upstream_products:
                                        if upstream:
                                            upstream_name = upstream["name"]
                                            net.add_node(upstream_name, label=upstream_name, title=upstream_name,
                                                        color="#ee6666", size=15, group=4)
                                            
                                            # 鎵惧埌鍏宠仈鐨勪骇鍝?
                                            for product in products:
                                                if product:
                                                    # 鏌ヨ浜у搧鍜屼笂娓镐骇鍝佺殑鍏崇郴
                                                    rel_query = """
                                                    MATCH (p:product {name: $product_name})-[r:涓婃父鏉愭枡]->(up:product {name: $upstream_name})
                                                    RETURN count(r) > 0 as has_relationship
                                                    """
                                                    rel_result = db.query(rel_query, {
                                                        "product_name": product["name"],
                                                        "upstream_name": upstream_name
                                                    })
                                                    
                                                    if rel_result and rel_result[0]["has_relationship"]:
                                                        net.add_edge(product["name"], upstream_name, title="涓婃父鏉愭枡")
                                    
                                    # 璁剧疆缃戠粶鍥鹃€夐」
                                    net.toggle_physics(True)
                                    net.set_options("""
                                    var options = {
                                      "physics": {
                                        "forceAtlas2Based": {
                                          "gravitationalConstant": -50,
                                          "centralGravity": 0.01,
                                          "springLength": 100,
                                          "springConstant": 0.08
                                        },
                                        "minVelocity": 0.75,
                                        "solver": "forceAtlas2Based"
                                      }
                                    }
                                    """)
                                    
                                    # 淇濆瓨鍒颁复鏃舵枃浠跺苟鏄剧ず
                                    try:
                                        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmpfile:
                                            temp_path = tmpfile.name
                                            net.save_graph(temp_path)
                                            
                                        with open(temp_path, 'r', encoding='utf-8') as f:
                                            html_content = f.read()
                                            
                                        components.html(html_content, height=700)
                                        st.success(f"鎴愬姛鐢熸垚 {selected_entity} 鐨勪骇涓氶摼")
                                        
                                        # 鍒犻櫎涓存椂鏂囦欢
                                        try:
                                            os.unlink(temp_path)
                                        except:
                                            pass
                                    except Exception as e:
                                        st.error(f"娓叉煋浜т笟閾惧浘琛ㄦ椂鍑洪敊: {str(e)}")
                                        logger.error(f"娓叉煋浜т笟閾惧浘琛ㄦ椂鍑洪敊: {str(e)}\n{traceback.format_exc()}")
                                else:
                                    st.warning("娌℃湁鎵惧埌浜т笟閾炬暟鎹?)
                            else:
                                st.info("浜т笟閾惧彲瑙嗗寲浠呮敮鎸佽涓氱被鍨嬬殑瀹炰綋")
                        except Exception as e:
                            st.error(f"鐢熸垚浜т笟閾炬椂鍑洪敊: {str(e)}")
                            logger.error(f"鐢熸垚浜т笟閾炬椂鍑洪敊: {str(e)}\n{traceback.format_exc()}")
                else:
                    st.warning(f"娌℃湁鎵惧埌涓?{selected_entity} 鐩稿叧鐨勮妭鐐瑰拰鍏崇郴")
            else:
                st.warning(f"娌℃湁鎵惧埌涓?{selected_entity} 鐩稿叧鐨勬暟鎹?)
        except Exception as e:
            st.error(f"鐢熸垚鍙鍖栨椂鍑洪敊: {str(e)}")
            logger.error(f"鐢熸垚鍙鍖栨椂鍑洪敊: {str(e)}\n{traceback.format_exc()}")
else:
    # 鏄剧ず浣跨敤璇存槑
    st.info("璇峰湪宸︿晶閫夋嫨瀹炰綋骞剁偣鍑?鐢熸垚鍙鍖?鎸夐挳鏉ユ煡鐪嬮珮绾х煡璇嗗浘璋卞彲瑙嗗寲")
    
    # 鏄剧ず绀轰緥鍥剧墖
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("缃戠粶鍥剧ず渚?)
        st.image("img/1.png", caption="鐭ヨ瘑鍥捐氨缃戠粶鍥剧ず渚?, use_container_width=True)
    
    with col2:
        st.subheader("灞傜骇鏍戠ず渚?)
        st.image("img/2.png", caption="鐭ヨ瘑鍥捐氨灞傜骇鏍戠ず渚?, use_container_width=True)

# 椤佃剼
st.markdown("---")
st.caption(f"鐭ヨ瘑鍥捐氨楂樼骇鍙鍖?| {datetime.now().strftime('%Y-%m-%d')}") 
