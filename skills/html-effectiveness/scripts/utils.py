import os

def resolve_references(references_list):
    """
    Recursively resolves local file/folder paths.
    - If a file is small (< 5KB), eagerly loads it directly into prompt context.
    - If a file is large (>= 5KB) or is a directory, only lists its path/metadata
      so the LLM can lazily request its contents via needs_references/requested_files.
    """
    context_str = ""
    if not references_list:
        return context_str
        
    for ref in references_list:
        ref_type = ref.get("type")
        path_or_url = ref.get("value", "").strip()
        if not path_or_url:
            continue
            
        if ref_type == "local":
            abs_path = os.path.abspath(path_or_url)
            # Security bounding check: must be inside workspace Cwd
            if abs_path.startswith(os.getcwd()) and os.path.exists(abs_path):
                if os.path.isfile(abs_path):
                    try:
                        file_size = os.path.getsize(abs_path)
                        # Small file limit: 5 KB (5120 bytes)
                        if file_size < 5120:
                            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                                context_str += f"### REFERENCE LOCAL FILE (EAGERLY LOADED): {path_or_url}\n```\n{f.read()}\n```\n\n"
                        else:
                            context_str += f"### REFERENCE LOCAL FILE (LAZY LOADED - LARGE FILE: {file_size} bytes): {path_or_url}\n"
                            context_str += f"This file is large. If you need to read its contents, you MUST set `needs_references: true` and add \"{path_or_url}\" to your `requested_files` list.\n\n"
                    except Exception as e:
                        context_str += f"### REFERENCE FILE ERROR: {path_or_url} (Could not read: {str(e)})\n\n"
                elif os.path.isdir(abs_path):
                    context_str += f"### REFERENCE LOCAL DIRECTORY (LAZY LOADED): {path_or_url}\n"
                    context_str += f"This directory's contents are not eagerly loaded. If you need to read any files inside this directory, search them first using interactive_search, then set `needs_references: true` and add the specific file path to your `requested_files` list.\n\n"
            else:
                context_str += f"### REFERENCE LOCAL PATH (RESTRICTED OR NOT FOUND): {path_or_url}\n\n"
        elif ref_type == "url":
            context_str += f"### REFERENCE EXTERNAL SOURCE/URL: {path_or_url}\n(Please use this URL/source repo as standard architectural reference.)\n\n"
            
    return context_str


def load_requested_files(requested_files, references_list):
    """
    Securely loads the contents of specific requested files.
    Ensures they are within the workspace boundary and authorized in the references list.
    """
    import os
    context_str = ""
    cwd = os.getcwd()
    
    # Extract authorized reference prefixes
    authorized_prefixes = []
    for ref in references_list:
        val = ref.get("value", "").strip()
        if val:
            authorized_prefixes.append(os.path.abspath(val))
            
    # Track total size of read content to prevent memory/token exhaustion
    total_bytes_read = 0
    MAX_SINGLE_FILE_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_TOTAL_SIZE = 10 * 1024 * 1024      # 10MB

    for rel_path in requested_files:
        clean_rel_path = rel_path.rstrip('/\\')
        if not clean_rel_path:
            clean_rel_path = rel_path

        abs_path = os.path.abspath(clean_rel_path)
        
        # Check if they requested an authorized prefix by its basename or exact path, or a sub-path
        for prefix in authorized_prefixes:
            prefix_basename = os.path.basename(prefix.rstrip('/\\'))
            if clean_rel_path == prefix_basename:
                abs_path = prefix
                break
            elif clean_rel_path.startswith(prefix_basename + '/'):
                remainder = clean_rel_path[len(prefix_basename)+1:]
                abs_path = os.path.join(prefix, remainder)
                break
            elif clean_rel_path == prefix.rstrip('/\\'):
                abs_path = prefix
                break
            elif clean_rel_path.startswith(prefix.rstrip('/\\') + '/'):
                abs_path = clean_rel_path
                break
        
        # Canonicalize both cwd, prefixes, and targets using realpath to prevent symlink bypasses
        abs_path = os.path.realpath(abs_path)
        canonical_cwd = os.path.realpath(cwd)
        
        # Authorization check: must be inside active workspace OR inside an authorized prefix
        authorized = False
        if abs_path == canonical_cwd or abs_path.startswith(canonical_cwd + os.sep):
            authorized = True
            
        for prefix in authorized_prefixes:
            canonical_prefix = os.path.realpath(prefix)
            if abs_path == canonical_prefix or abs_path.startswith(canonical_prefix + os.sep):
                authorized = True
                break
                
        if not authorized:
            context_str += f"### ACCESS DENIED: {rel_path} is not in the imported references list or active workspace.\n\n"
            continue
            
        if not os.path.exists(abs_path):
            # Attempt to search for the file inside the authorized prefixes
            import glob
            found_paths = []
            for prefix in authorized_prefixes:
                canonical_prefix = os.path.realpath(prefix)
                # Recursive glob search for filename matching the requested string
                search_pattern = os.path.join(canonical_prefix, "**", os.path.basename(rel_path))
                found_paths.extend(glob.glob(search_pattern, recursive=True))
                # Also search for partial matches if no exact match is found
                if not found_paths:
                    search_pattern_partial = os.path.join(canonical_prefix, "**", f"*{rel_path}*")
                    found_paths.extend(glob.glob(search_pattern_partial, recursive=True))
            
            # Filter to valid paths (files or directories)
            found_valid = [os.path.realpath(p) for p in found_paths if os.path.exists(p)]
            if found_valid:
                potential_path = found_valid[0]
                if potential_path.startswith(canonical_cwd):
                    abs_path = potential_path
                    context_str += f"### SEARCHED AND FOUND ALTERNATE PATH: {os.path.relpath(abs_path, cwd)}\n"
                else:
                    context_str += f"### FILE NOT FOUND (Search matched out-of-boundary path): {rel_path}\n\n"
                    continue
            else:
                context_str += f"### FILE NOT FOUND (Search failed): {rel_path}\n\n"
                continue
            
        if os.path.isdir(abs_path):
            # Return a directory tree listing
            tree = []
            ignore_dirs = {'.git', '.vscode', '__pycache__', 'node_modules', 'build', 'dist'}
            ignore_files = {'.DS_Store'}
            for root, dirs, files in os.walk(abs_path):
                # skip hidden and noisy dirs
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignore_dirs]
                for f in files:
                    if not f.startswith('.') and f not in ignore_files:
                        real_f_path = os.path.realpath(os.path.join(root, f))
                        if real_f_path.startswith(canonical_cwd):
                            tree.append(os.path.relpath(real_f_path, cwd))
            
            if len(tree) > 100:
                tree_str = "\n".join(tree[:100]) + f"\n...and {len(tree)-100} more files."
            else:
                tree_str = "\n".join(tree)
                
            context_str += f"### DIRECTORY CONTENTS FOR: {rel_path}\n{tree_str}\n\n"
            context_str += f"(Please request specific file paths from the list above if you need their contents.)\n\n"
            continue
            
        # 3. Read content with size restrictions
        try:
            file_size = os.path.getsize(abs_path)
            if file_size > MAX_SINGLE_FILE_SIZE:
                context_str += f"### WARNING: File {rel_path} is too large ({file_size / (1024*1024):.2f}MB). Only the first 2MB will be loaded to prevent token overflow.\n"
                read_limit = MAX_SINGLE_FILE_SIZE
            else:
                read_limit = -1
                
            if total_bytes_read >= MAX_TOTAL_SIZE:
                context_str += f"### WARNING: Cumulative loaded reference size exceeded 10MB safety limit. Skipping content read for {rel_path}.\n\n"
                continue

            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                if read_limit > 0:
                    content = f.read(read_limit)
                    content += "\n...[TRUNCATED due to 2MB limit]..."
                else:
                    content = f.read()
                    
            bytes_read = len(content.encode('utf-8', errors='ignore'))
            total_bytes_read += bytes_read
            
            context_str += f"### CONTENTS OF REFERENCE FILE: {os.path.relpath(abs_path, cwd)}\n```\n{content}\n```\n\n"
        except Exception as e:
            context_str += f"### ERROR READING FILE {rel_path}: {str(e)}\n\n"
            
    return context_str
