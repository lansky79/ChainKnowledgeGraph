import json
import sys

def check_json_file(filepath):
    data = []
    errors = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    print(f'Error at line {i}: {line[:50]}... - {str(e)}')
                    errors += 1
                    
        print(f'Successfully parsed {len(data)} lines, found {errors} errors')
        
        if len(data) > 0:
            print("\nSample data:")
            for i, item in enumerate(data[:5]):
                print(f"Item {i+1}: {item}")
                
    except Exception as e:
        print(f"Error opening file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_json_file(sys.argv[1])
    else:
        print("Usage: python check_json.py <json_file_path>") 