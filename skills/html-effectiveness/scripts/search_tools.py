import os, shlex, subprocess, json

def interactive_search(mode: str, query: str, path: str, offset: int = 0, limit: int = 100) -> str:
    """Perform codebase search using ripgrep, glob, or lsp with limits and pagination.
    
    Args:
        mode: Search mode, one of 'regex' or 'glob'. 'lsp' is not currently supported.
        query: Search pattern or glob string (e.g. "*.py", "import os")
        path: Target directory or file path to search within.
        offset: Pagination offset.
        limit: Pagination limit.
    """
    import shlex, subprocess, json
    
    safe_path = shlex.quote(path)
    safe_query = shlex.quote(query)
    
    MAX_LINES = 2000
    MAX_BYTES = 50 * 1024
    
    if mode == "regex":
        cmd = f"rg --json -e {safe_query} {safe_path}"
    elif mode == "glob":
        cmd = f"find {safe_path} -name {safe_query} -not -path '*/.git/*' -not -path '*/node_modules/*'"
    else:
        return json.dumps({"status": "error", "message": f"unsupported mode: {mode}"})
        
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout
        
        if len(output) > MAX_BYTES or output.count('\n') > MAX_LINES:
            temp_file = "/tmp/search_results_full.json"
            with open(temp_file, "w") as f:
                f.write(output)
            return json.dumps({
                "status": "truncated",
                "preview": output[:1000] + "... (truncated)",
                "full_results_path": temp_file
            })
            
        return json.dumps({"status": "success", "results": output[:MAX_BYTES]})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def list_directory(path: str) -> str:
    """Lists all files and subdirectories in a given directory path. (Equivalent to `ls`)
    
    Args:
        path: The relative or absolute path of the directory to list.
    """
    import os, json
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        return json.dumps({"status": "error", "message": f"Directory not found: {path}"})
    if not os.path.isdir(abs_path):
        return json.dumps({"status": "error", "message": f"Path is not a directory: {path}"})
        
    try:
        entries = os.listdir(abs_path)
        return json.dumps({"status": "success", "path": abs_path, "entries": entries})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def glob_search(pattern: str, recursive: bool = True) -> str:
    """Finds files matching a specified glob pattern. (Equivalent to `glob` or `find`)
    
    Args:
        pattern: The glob pattern to search for (e.g., '**/*.py', 'src/*/*.js', 'BaseLine-EveryThing').
        recursive: Whether to search recursively if the pattern contains '**'. Default is True.
    """
    import glob, json
    try:
        # Prevent huge glob results by limiting output
        results = glob.glob(pattern, recursive=recursive)
        
        # If no results but it's a simple string, maybe try wrapping it in **/*string*
        if not results and '*' not in pattern:
            results = glob.glob(f"**/*{pattern}*", recursive=recursive)
            
        return json.dumps({
            "status": "success", 
            "count": len(results), 
            "results": results[:100] + (['...(truncated)'] if len(results) > 100 else [])
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
