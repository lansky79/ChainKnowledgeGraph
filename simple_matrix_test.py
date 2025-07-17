#!/usr/bin/env python3
# coding: utf-8
# File: simple_matrix_test.py
# 简单的矩阵测试

import matplotlib.pyplot as plt
import numpy as np

def test_simple_matrix():
    """测试简单的矩阵显示"""
    
    # 创建一个简单的测试矩阵
    companies = ["华为", "阿里巴巴", "腾讯", "百度"]
    products = ["智能手机", "淘宝", "微信", "百度搜索", "5G基站"]
    
    # 创建矩阵 (4x5)
    matrix = np.zeros((len(companies), len(products)))
    
    # 手动设置一些关系
    matrix[0, 0] = 1  # 华为 -> 智能手机
    matrix[0, 4] = 1  # 华为 -> 5G基站
    matrix[1, 1] = 1  # 阿里巴巴 -> 淘宝
    matrix[2, 2] = 1  # 腾讯 -> 微信
    matrix[3, 3] = 1  # 百度 -> 百度搜索
    
    print("矩阵内容:")
    print(matrix)
    print(f"非零元素数量: {np.sum(matrix > 0)}")
    
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 显示矩阵
    im = ax.imshow(matrix, cmap="Blues")
    
    # 设置坐标轴标签
    ax.set_xticks(np.arange(len(products)))
    ax.set_yticks(np.arange(len(companies)))
    ax.set_xticklabels(products, fontsize=10)
    ax.set_yticklabels(companies, fontsize=10)
    
    # 添加标题
    ax.set_title("测试公司-产品关系矩阵", fontsize=14)
    
    # 在矩阵中添加文本标签
    for i in range(len(companies)):
        for j in range(len(products)):
            if matrix[i, j] > 0:
                # 使用明显的标记
                ax.text(j, i, "●", ha="center", va="center", color="red", fontsize=16, weight="bold")
                print(f"添加标记: [{i}][{j}] = {companies[i]} -> {products[j]}")
    
    # 旋转X轴标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # 添加网格线
    ax.set_xticks(np.arange(-.5, len(products), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(companies), 1), minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图片
    plt.savefig("test_matrix.png", dpi=150, bbox_inches='tight')
    print("测试矩阵已保存为 test_matrix.png")
    
    # 显示图形
    plt.show()

if __name__ == "__main__":
    test_simple_matrix()