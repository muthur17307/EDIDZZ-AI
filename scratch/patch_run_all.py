from pathlib import Path

target = Path("run_all.py")
text = target.read_text(encoding="utf-8")

old_func = """def connect_pipeline_paths():
    \"\"\"Adds backend and standalone pipeline directories to sys.path and PYTHONPATH.\"\"\"
    print("\\n[4/5] Connecting pipeline modules and FastAPI backend...")
    for path in [BACKEND_DIR, STANDALONE_PIPELINE_DIR, ROOT_DIR]:
        path_str = str(path)
        if path.exists() and path_str not in sys.path:
            sys.path.insert(0, path_str)

    current_pythonpath = os.environ.get("PYTHONPATH", "")
    new_paths = [str(BACKEND_DIR), str(STANDALONE_PIPELINE_DIR), str(ROOT_DIR)]
    os.environ["PYTHONPATH"] = os.pathsep.join(new_paths + ([current_pythonpath] if current_pythonpath else []))
    print(f"      Connected pipeline modules: EditAI/backend & EDIT-AI-PIPELINE--main")"""

new_func = """def connect_pipeline_paths():
    \"\"\"Adds backend directory to sys.path and PYTHONPATH.\"\"\"
    print("\\n[4/5] Connecting pipeline modules and FastAPI backend...")
    # BACKEND_DIR must be FIRST so EditAI/backend/app is always imported
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))
    if str(ROOT_DIR) not in sys.path:
        sys.path.append(str(ROOT_DIR))

    current_pythonpath = os.environ.get("PYTHONPATH", "")
    new_paths = [str(BACKEND_DIR), str(ROOT_DIR)]
    os.environ["PYTHONPATH"] = os.pathsep.join(new_paths + ([current_pythonpath] if current_pythonpath else []))
    print(f"      Connected pipeline modules: EditAI/backend")"""

assert old_func in text, "old_func not found"
text = text.replace(old_func, new_func, 1)

# Also ensure uvicorn runs with cwd=BACKEND_DIR
old_run = 'uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)'
new_run = 'os.chdir(str(BACKEND_DIR))\n    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)'
assert old_run in text, "old_run not found"
text = text.replace(old_run, new_run, 1)

target.write_text(text, encoding="utf-8")
print("run_all.py patched successfully!")

