import json
import sys
import os

def fix_json_file(filepath):
    print(f"正在修复文件: {filepath}")
    
    # 读取文件内容，使用 utf-8-sig 编码来处理 BOM
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        # 计算有效行数
        valid_lines = [line.strip() for line in lines if line.strip()]
        print(f"文件共有 {len(valid_lines)} 行有效数据")
        
        # 创建备份文件
        backup_file = filepath + '.bak'
        if os.path.exists(backup_file):
            os.remove(backup_file)
        os.rename(filepath, backup_file)
        print(f"已创建备份文件: {backup_file}")
        
        # 写入修复后的文件，使用 utf-8 编码（无 BOM）
        with open(filepath, 'w', encoding='utf-8') as f:
            for line in valid_lines:
                try:
                    # 验证每行是否为有效的 JSON
                    json_obj = json.loads(line)
                    f.write(json.dumps(json_obj, ensure_ascii=False) + '\n')
                except Exception as e:
                    print(f"警告: 跳过无效行: {line[:50]}... - {str(e)}")
        
        print(f"文件修复完成: {filepath}")
        
        # 验证修复后的文件
        errors = 0
        valid_count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                try:
                    json.loads(line.strip())
                    valid_count += 1
                except Exception as e:
                    print(f"验证错误 (行 {i}): {str(e)}")
                    errors += 1
        
        print(f"验证结果: {valid_count} 行有效, {errors} 行错误")
        
    except Exception as e:
        print(f"修复过程出错: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fix_json_file(sys.argv[1])
    else:
        print("用法: python fix_json.py <json_file_path>") 