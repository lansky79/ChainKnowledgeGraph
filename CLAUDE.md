# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Language Preference
**请使用中文进行所有交流和说明。** 这个项目的界面、文档和用户主要使用中文，因此在协助开发时应该用中文来交流，便于理解和维护。

## System Environment
**操作系统：Windows** - 执行命令时请使用Windows语法，不要使用Unix/Linux命令。例如：
- 使用 `dir` 而不是 `ls`
- 使用 `type` 而不是 `cat`
- 使用 `del` 而不是 `rm`
- 路径分隔符使用反斜杠 `\`
- 批处理文件使用 `.bat` 扩展名

## Project Overview

This is a knowledge graph visualization system built with Streamlit and Neo4j that visualizes relationships between companies, industries, and products. The system supports multiple visualization types including interactive network graphs, ECharts graphs, hierarchical trees, and relationship matrices.

## Key Commands

### Application Startup
- **Primary**: `python -m streamlit run app.py` - Start the main application
- **Windows**: `start_app.bat` - Automated startup script for Windows that handles virtual environment activation and dependency installation
- **Alternative startup scripts**:
  - `streamlit_only.bat` - Start Streamlit only
  - `run_simple_app.bat` - Run simple version
  - `start_all.bat` - Start all services

### Development and Testing
- **Dependencies**: `pip install -r requirements.txt` - Install required packages
- **Virtual Environment**: The project uses `kg_env` virtual environment (Windows batch scripts handle activation)
- **Database Test**: Run `check_neo4j_connection.py` to verify Neo4j connectivity

### Data Management
- **Import Sample Data**: Use the "导入示例数据" button in the sidebar or run data import scripts
- **Demo Data Creation**: Various demo scripts like `create_demo_data.py`, `create_it_service_demo.py`

## Architecture and Structure

### Core Application Architecture
- **Main Entry**: `app.py` - Primary Streamlit application with network visualization
- **Multi-page Structure**: Streamlit pages in `pages/` directory:
  - `01_数据导入.py` - Data import functionality  
  - `02_高级可视化.py` - Advanced visualization features

### Database Layer
- **Database**: Neo4j graph database (default: bolt://localhost:7687)
- **Connection**: `utils/db_connector.py` - Neo4j connection management using py2neo
- **Handler**: `src/neo4j_handler.py` - Additional Neo4j operations

### Data Processing
- **Data Processor**: `utils/data_processor.py` - Process Neo4j results for visualization
- **Entity Types**: Three main entity types with specific node labels:
  - `company` - Company entities
  - `industry` - Industry entities  
  - `product` - Product entities

### Visualization Components
- **Network Visualization**: `visualizers/network_viz.py` - Interactive network graphs using pyvis and ECharts
- **Supported Formats**:
  - Interactive network graphs (pyvis)
  - ECharts network graphs
  - Hierarchical trees (industry only)
  - Relationship matrices
  - Supply chain visualizations

### Configuration Management
- **Main Config**: `config.py` - Loads configuration from JSON files
- **Platform Detection**: Automatically detects Windows and loads appropriate config
- **Config Files**: 
  - `config_windows.json` (Windows-specific)
  - `config.json` (default)

### Data Storage
- **Sample Data**: `data/` directory contains JSON files:
  - `company.json` - Company entities
  - `industry.json` - Industry entities
  - `product.json` - Product entities
  - Relationship files (e.g., `company_industry.json`)

### Utilities
- **Logging**: `utils/logger.py` - Centralized logging setup
- **Log Storage**: `logs/` directory with dated log files

## Key Technical Details

### Entity Relationships
- **Company ↔ Industry**: `所属行业` relationship
- **Company ↔ Product**: `主营产品` relationship  
- **Product ↔ Product**: `上游材料` relationship
- **Industry ↔ Industry**: `上级行业` relationship

### Visualization Groups
- Group 0: Industries (green color #2ca02c)
- Group 1: Companies (orange color #ff7f0e) 
- Group 2: Products (red color #d62728)

### Data Import Process
1. Clear existing data with `MATCH (n) DETACH DELETE n`
2. Create nodes by entity type using CREATE statements
3. Establish relationships using MATCH and CREATE patterns
4. Support for both manual JSON upload and sample data import

### Neo4j Query Patterns
- Uses parameterized Cypher queries for security
- Implements relationship depth traversal (1-3 levels)
- Caches entity lists with TTL for performance
- Handles large datasets with batch processing

## Development Notes

### Error Handling
- Comprehensive logging throughout the application
- Graceful degradation when components fail
- User-friendly error messages in Streamlit interface

### Performance Considerations
- Streamlit caching for database connections and entity lists
- Temporary file cleanup for network visualizations
- Batch size configuration for large data imports

### Internationalization
- Primary language: Chinese (interface text and entity names)
- All documentation and labels use Chinese characters
- UTF-8 encoding throughout