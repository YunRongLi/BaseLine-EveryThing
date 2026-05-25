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
