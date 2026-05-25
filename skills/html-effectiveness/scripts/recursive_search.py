import os, time, re, json, fnmatch

def extract_and_resolve_paths(query: str, workspace_root: str) -> list[str]:
    """Extract and resolve potential absolute, relative, or home-directory file paths in the query."""
    tokens = re.split(r'[\s\"\'\(\)\[\]\{\}\,\;\`\<\>]', query)
    resolved_paths = []
    
    for token in tokens:
        token = token.strip()
        if not token:
            continue
            
        has_separator = '/' in token
        has_extension = any(token.endswith(ext) for ext in ['.py', '.ts', '.tsx', '.js', '.c', '.cpp', '.h', '.hpp', '.go', '.java', '.md', '.html', '.json', '.sh', '.ps1', '.base', '.canvas'])
        
        if not (has_separator or has_extension):
            continue
            
        resolved = None
        if token.startswith('~/'):
            resolved = os.path.abspath(os.path.expanduser(token))
        elif os.path.isabs(token):
            resolved = os.path.abspath(token)
        else:
            resolved = os.path.abspath(os.path.join(workspace_root, token))
            
        if resolved and os.path.isfile(resolved):
            try:
                rel_path = os.path.relpath(resolved, workspace_root)
            except ValueError:
                # In case paths are on different drives in some OS, though we are on Linux
                continue
            exclude_dirs = {'.git', 'node_modules', '.tmp', '.gemini', '__pycache__', 'artifacts', 'brain'}
            parts = rel_path.split(os.sep)
            if not any(part in exclude_dirs for part in parts):
                if rel_path not in resolved_paths:
                    resolved_paths.append(rel_path)
                    
    return resolved_paths

def perform_local_recursive_search(query: str, target_count: int = 6, max_iterations: int = 3, weights: dict = None, language: str = 'en') -> dict:
    """Perform a heuristic-driven, semantic recursive search for files in the workspace.
    
    This tool decomposes the query into core keywords and synonyms, then searches the 
    local workspace directory iteratively. It scores files based on relevance (keyword matches),
    priority (important architectural directories), and signal-to-noise ratio (source code preferred).
    Use this tool when you need broad context or when exact regex/glob searches are insufficient.
    
    Args:
        query: The semantic search query (e.g. "authentication logic", "database schema").
        target_count: Maximum number of top-scored files to return. Defaults to 6.
        max_iterations: Maximum number of expansion rounds. Defaults to 3.
        weights: Dictionary of scoring weights (e.g. {"rel": 50, "pri": 30, "snr": 20}). Defaults to None.
        language: Language for internal logging ('en' or 'zh'). Defaults to 'en'.
        
    Returns:
        A dictionary containing the search status, metrics, step logs, and the top matched file results.
    """
    import time
    import fnmatch
    import os
    import re
    import json
    
    start_time = time.time()
    print(f"\n🔍 [Search] Starting recursive search for query: '{query}'")
    
    workspace_root = os.getcwd()
    resolved_paths = extract_and_resolve_paths(query, workspace_root)
    
    if weights is None:
        weights = {"rel": 50, "pri": 30, "snr": 20}
        
    w_rel = weights.get("rel", 50)
    w_pri = weights.get("pri", 30)
    w_snr = weights.get("snr", 20)
    
    # Normalize weights
    total_w = w_rel + w_pri + w_snr
    if total_w > 0:
        w_rel = (w_rel / total_w) * 100
        w_pri = (w_pri / total_w) * 100
        w_snr = (w_snr / total_w) * 100
    else:
        w_rel, w_pri, w_snr = 50.0, 30.0, 20.0

    # Phase 1: Decomposition
    keywords = []
    synonyms = []
    api_decomposed = False
    
    # Local fallback parsing
    words = re.findall(r'[a-zA-Z0-9\u4e00-\u9fa5]+', query)
    stopwords_en = {'find', 'all', 'files', 'implementing', 'logic', 'with', 'the', 'a', 'an', 'of', 'and', 'or', 'in', 'to', 'for', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'module', 'codebase', 'project', 'search', 'mechanism', 'using', 'based', 'on'}
    stopwords_zh = {'找出', '所有', '實現', '的', '和', '與', '或', '在', '中', '於', '邏輯', '模組', '功能', '代碼', '檔案', '專案', '搜尋', '機制', '使用', '基於', '我們'}
    
    local_keywords = []
    for w in words:
        w_low = w.lower()
        if w_low not in stopwords_en and w not in stopwords_zh and len(w) > 1:
            local_keywords.append(w_low)
            
    # Local synonyms dictionary
    synonyms_map = {
        "login": ["auth", "signin", "credentials", "session", "authenticate", "登入", "驗證"],
        "auth": ["login", "session", "jwt", "token", "credentials", "verification", "權限"],
        "obsidian": ["vault", "note", "markdown", "para", "link", "筆記", "卡片"],
        "git": ["commit", "branch", "workflow", "repo", "分支", "提交"],
        "html": ["css", "javascript", "template", "dom", "ui", "網頁", "介面"],
        "c++": ["cpp", "core", "guideline", "class", "pointer", "指標"],
        "bmc": ["redfish", "ipmi", "sensor", "firmware", "d-bus", "mctp", "pldm"],
        "kernel": ["review", "driver", "module", "device", "sysfs"],
        "search": ["glob", "grep", "recursive", "find", "filter", "遞迴", "搜尋"]
    }
    
    # Try calling LLM first if API key is present
    if os.environ.get("GEMINI_API_KEY"):
        try:
            from google import genai
            from google.genai import types
            client = genai.Client()
            decomp_prompt = f"""You are a query decomposition agent. Analyze this search query for a local workspace: "{query}".
Return a JSON object containing:
1. "keywords": List of 3-5 lowercase core search keywords (English or Chinese).
2. "synonyms": List of 3-5 lowercase synonyms/related words for horizontal/semantic expansion.
3. "paths": List of 1-3 directory paths in the workspace most likely to contain these files (e.g. "skills", "rules", "workflows", "src").

Format your response exactly as raw JSON, no markdown codeblocks, no extra explanation."""
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=decomp_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            data = json.loads(response.text.strip())
            keywords = [k.lower() for k in data.get("keywords", []) if k]
            synonyms = [s.lower() for s in data.get("synonyms", []) if s]
            target_paths = data.get("paths", ["."])
            api_decomposed = True
        except Exception:
            pass
            
    if not api_decomposed:
        keywords = list(set(local_keywords))
        target_paths = ["."]
        for kw in keywords:
            if kw in synonyms_map:
                synonyms.extend(synonyms_map[kw])
        synonyms = list(set(synonyms) - set(keywords))

    step_logs = {}
    
    if language == 'zh':
        step_logs["step1"] = {
            "status": "completed",
            "details": f"問題分解完成。<br>核心關鍵字: {', '.join(keywords)}<br>潛在語意擴充詞: {', '.join(synonyms) if synonyms else '無'}<br>解析出的路徑: {', '.join(resolved_paths) if resolved_paths else '無'}<br>初始目標目錄: {', '.join(target_paths)}"
        }
    else:
        step_logs["step1"] = {
            "status": "completed",
            "details": f"Query decomposition completed successfully.<br>Core Keywords: {', '.join(keywords)}<br>Semantic Synonyms: {', '.join(synonyms) if synonyms else 'None'}<br>Resolved Paths: {', '.join(resolved_paths) if resolved_paths else 'None'}<br>Initial Paths: {', '.join(target_paths)}"
        }
        
    active_keywords = list(keywords)
    scanned_count = 0
    filtered_count = 0
    rounds_taken = 0
    all_candidates = {}
    
    for rel_path in resolved_paths:
        all_candidates[rel_path] = {
            "path": rel_path,
            "relevance": 100.0,
            "priority": 100.0,
            "snr": 100.0,
            "score": 100.0,
            "status": "Pass"
        }
        filtered_count += 1
    
    for round_idx in range(1, max_iterations + 1):
        rounds_taken = round_idx
        
        if round_idx > 1:
            added_keywords = []
            for syn in synonyms:
                if syn not in active_keywords:
                    active_keywords.append(syn)
                    added_keywords.append(syn)
            
            target_paths = ["."]
            
            if language == 'zh':
                step_logs[f"round{round_idx}_expansion"] = {
                    "status": "expanded",
                    "details": f"觸發第 {round_idx} 輪遞迴擴充！擴充語意關鍵字: {', '.join(added_keywords) if added_keywords else '無'}。搜尋範圍已擴大至整個專案目錄。"
                }
            else:
                step_logs[f"round{round_idx}_expansion"] = {
                    "status": "expanded",
                    "details": f"Triggered Round {round_idx} Recursive Expansion! Added semantic keywords: {', '.join(added_keywords) if added_keywords else 'None'}. Expanded target paths to entire workspace."
                }
            
            print(f"🔍 [Search] Iteration {round_idx}: expanded search terms: {added_keywords}")

        found_files = []
        exclude_dirs = {'.git', 'node_modules', '.tmp', '.gemini', '__pycache__', 'artifacts', 'brain'}
        valid_exts = {'.py', '.ts', '.tsx', '.js', '.c', '.cpp', '.h', '.hpp', '.go', '.java', '.md', '.html', '.json', '.sh', '.ps1', '.base', '.canvas'}
        
        for root_dir in target_paths:
            for root, dirs, files in os.walk(root_dir):
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in valid_exts:
                        filepath = os.path.relpath(os.path.join(root, file), os.getcwd())
                        if filepath not in all_candidates:
                            found_files.append(filepath)
                            
        for filepath in found_files:
            scanned_count += 1
            abs_filepath = os.path.abspath(filepath)
            
            content = ""
            try:
                with open(abs_filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(50000)
            except Exception:
                continue
                
            matched_kws = []
            kw_frequency = 0
            for kw in active_keywords:
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                matches = pattern.findall(content)
                filename_matches = pattern.findall(filepath)
                
                if matches or filename_matches:
                    matched_kws.append(kw)
                    kw_frequency += len(matches) + len(filename_matches) * 5
                    
            if not active_keywords:
                relevance_score = 0.0
            else:
                base_rel = (len(matched_kws) / len(active_keywords)) * 70
                freq_bonus = min(30.0, kw_frequency * 1.5)
                relevance_score = min(100.0, base_rel + freq_bonus)
                
            if relevance_score == 0:
                continue
                
            priority_score = 70.0
            filepath_low = filepath.lower()
            
            if any(p in filepath_low for p in ['skills/', 'rules/', 'workflows/']):
                priority_score = 90.0
            elif any(p in filepath_low for p in ['/tests/', '/mock/', 'packages/', 'tmp/', 'scratch/']):
                priority_score = 40.0
                
            if any(kw in os.path.basename(filepath_low) for kw in active_keywords):
                priority_score = min(100.0, priority_score + 15.0)
                
            ext = os.path.splitext(filepath)[1].lower()
            if ext in ['.py', '.ts', '.js', '.c', '.cpp', '.go', '.java']:
                snr_score = 95.0
            elif ext in ['.md'] and any(p in filepath_low for p in ['rules/', 'skills/']):
                snr_score = 90.0
            elif ext in ['.md', '.html', '.base', '.canvas']:
                snr_score = 65.0
            elif ext in ['.json', '.yaml', '.yml']:
                snr_score = 50.0
            else:
                snr_score = 40.0
                
            if 'test' in filepath_low or 'mock' in filepath_low:
                snr_score = max(10.0, snr_score - 50.0)
                
            agg_score = (relevance_score * w_rel + priority_score * w_pri + snr_score * w_snr) / 100.0
            agg_score = round(agg_score, 1)
            
            status = "Pass" if agg_score >= 60.0 else "Fail"
            if status == "Pass":
                filtered_count += 1
                
            all_candidates[filepath] = {
                "path": filepath,
                "relevance": round(relevance_score, 1),
                "priority": round(priority_score, 1),
                "snr": round(snr_score, 1),
                "score": agg_score,
                "status": status
            }

        converged_candidates = [c for c in all_candidates.values() if c["score"] >= 60.0]
        
        print(f"🔍 [Search] Iteration {round_idx} found {len(found_files)} matches. Converged candidates: {len(converged_candidates)} (Target: {target_count})")
        
        if language == 'zh':
            round_details = f"第 {round_idx} 輪掃描：掃描了 {len(found_files)} 個新檔案，當前累計評估 {scanned_count} 個檔案。<br>"
            round_details += f"符合收斂門檻 (分數 >= 60) 的候選檔案數量: <strong>{len(converged_candidates)}</strong> (目標: {target_count})。<br>"
            if len(converged_candidates) >= target_count:
                round_details += "<strong>收斂成功！</strong> 候選檔案數量已達標，停止遞迴搜尋。"
                step_logs[f"round{round_idx}_convergence"] = {
                    "status": "completed",
                    "details": round_details
                }
                break
            else:
                round_details += f"收斂失敗。候選檔案數 {len(converged_candidates)} < 目標數 {target_count}。"
                if round_idx == max_iterations:
                    round_details += " 已達最大遞迴次數，強制結束搜尋。"
                step_logs[f"round{round_idx}_convergence"] = {
                    "status": "failed",
                    "details": round_details
                }
        else:
            round_details = f"Round {round_idx} Scan: Evaluated {len(found_files)} new files, total evaluated: {scanned_count}.<br>"
            round_details += f"Candidates meeting convergence threshold (Score >= 60): <strong>{len(converged_candidates)}</strong> (Target: {target_count}).<br>"
            if len(converged_candidates) >= target_count:
                round_details += "<strong>Convergence Succeeded!</strong> Found sufficient target candidates, stopping recursive search."
                step_logs[f"round{round_idx}_convergence"] = {
                    "status": "completed",
                    "details": round_details
                }
                break
            else:
                round_details += f"Convergence Failed. Candidate count {len(converged_candidates)} < Target {target_count}."
                if round_idx == max_iterations:
                    round_details += " Reached maximum recursion depth, forcing termination."
                step_logs[f"round{round_idx}_convergence"] = {
                    "status": "failed",
                    "details": round_details
                }

    sorted_candidates = sorted(all_candidates.values(), key=lambda x: x["score"], reverse=True)
    final_results = sorted_candidates[:target_count]
    
    elapsed_time = round((time.time() - start_time) * 1000, 1)
    
    print(f"🔍 [Search] Completed with {len(final_results)} top results in {elapsed_time:.2f}ms.\\n")
    
    if language == 'zh':
        step_logs["step5"] = {
            "status": "completed",
            "details": f"最終收斂完成。<br>搜尋總耗時: {elapsed_time} 毫秒<br>評估檔案總數: {scanned_count}<br>符合門檻檔案數: {len([c for c in sorted_candidates if c['score'] >= 60.0])}<br>最終篩選出最具價值的 {len(final_results)} 個候選檔案並完成排序。"
        }
    else:
        step_logs["step5"] = {
            "status": "completed",
            "details": f"Final convergence and deduplication completed.<br>Total Search Time: {elapsed_time} ms<br>Total Files Evaluated: {scanned_count}<br>Files Meeting Threshold: {len([c for c in sorted_candidates if c['score'] >= 60.0])}<br>Selected top {len(final_results)} candidates sorted by priority."
        }
        
    return {
        "status": "success",
        "scanned": scanned_count,
        "filtered": filtered_count,
        "rounds": rounds_taken,
        "time_ms": elapsed_time,
        "step_logs": step_logs,
        "results": final_results
    }
