import os
import sys
import socket

def check_file_exists(path, name):
    if os.path.exists(path):
        print(f"[PASS] {name} exists at {path}")
        return True
    else:
        print(f"[FAIL] {name} not found at {path}")
        return False

def check_directory_exists(path, name):
    if os.path.isdir(path):
        count = len([f for f in os.listdir(path) if f.endswith('.json')])
        print(f"[PASS] {name} exists at {path} with {count} JSON files")
        if count == 0:
            print(f"[WARN] {name} is empty")
        return True
    else:
        print(f"[FAIL] {name} not found at {path}")
        return False

def check_import(module_name):
    try:
        __import__(module_name)
        print(f"[PASS] Import '{module_name}' successful")
        return True
    except ImportError:
        print(f"[FAIL] Import '{module_name}' failed")
        return False

def check_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            print(f"[PASS] Port {port} is free")
            return True
        except socket.error:
            print(f"[FAIL] Port {port} is already in use")
            return False

def check_model_cache():
    # Huggingface cache usually stores downloaded models here
    cache_dir = os.environ.get("HUGGINGFACE_HUB_CACHE", os.path.expanduser("~/.cache/huggingface/hub"))
    model_name = "models--intfloat--multilingual-e5-small"
    model_path = os.path.join(cache_dir, model_name)
    if os.path.isdir(model_path) and len(os.listdir(model_path)) > 0:
        print(f"[PASS] Dense model cache '{model_name}' found locally")
        return True
    else:
        print(f"[WARN] Dense model cache '{model_name}' not found at {cache_dir}. It may require internet download.")
        return False

def main():
    print("--- UniTrust V2 Preflight Check ---")
    
    has_failure = False
    
    # 1. Check unitrust.db
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "unitrust.db")
    if not check_file_exists(db_path, "unitrust.db"):
        has_failure = True
    
    # 2. Check annotations
    annotations_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "annotations", "batch_001")
    if not check_directory_exists(annotations_path, "Reviewed annotations directory"):
        has_failure = True
    
    # 3. Check demo cases
    demo_cases_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "demo_cases.py")
    if not check_file_exists(demo_cases_path, "Demo cases module"):
        has_failure = True
    
    # 4. Check python imports
    for mod in ["fastapi", "streamlit", "pydantic", "httpx", "sentence_transformers"]:
        if not check_import(mod):
            has_failure = True
        
    # 5. Check ports
    if not check_port_free(8000): has_failure = True
    if not check_port_free(8501): has_failure = True
    
    # 6. Check local model cache
    if not check_model_cache():
        has_failure = True
    
    print("-----------------------------------")
    if has_failure:
        print("Preflight check FAILED. The system will not start.")
        sys.exit(1)
    else:
        print("Preflight check PASSED (with possible warnings).")
        sys.exit(0)

if __name__ == "__main__":
    main()
