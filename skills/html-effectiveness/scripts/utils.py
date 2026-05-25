import os

def resolve_references(references_list):
    """
    Recursively resolves local file/folder paths and reads their content,
    or formats URLs as high-quality architectural context.
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
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            context_str += f"### REFERENCE LOCAL FILE: {path_or_url}\n```\n{f.read()}\n```\n\n"
                    except Exception as e:
                        context_str += f"### REFERENCE FILE ERROR: {path_or_url} (Could not read: {str(e)})\n\n"
                elif os.path.isdir(abs_path):
                    context_str += f"### REFERENCE LOCAL DIRECTORY: {path_or_url}\n"
                    context_str += f"This is a directory. Its contents are not auto-loaded to save context space.\n"
                    context_str += f"You MUST use the `interactive_search` tool with `path=\"{path_or_url}\"` to explore its files using `glob` or `regex` modes.\n\n"
            else:
                context_str += f"### REFERENCE LOCAL PATH (RESTRICTED OR NOT FOUND): {path_or_url}\n\n"
        elif ref_type == "url":
            context_str += f"### REFERENCE EXTERNAL SOURCE/URL: {path_or_url}\n(Please use this URL/source repo as standard architectural reference.)\n\n"
            
    return context_str
