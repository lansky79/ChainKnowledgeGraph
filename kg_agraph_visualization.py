import streamlit as st
import pandas as pd
import numpy as np
import logging
from streamlit_agraph import agraph, Node, Edge, Config

# 设置日志
logger = logging.getLogger("KG_Agraph_Visualization")
