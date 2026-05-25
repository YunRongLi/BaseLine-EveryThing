import os
import re
import json

def apply_patch(patch: str) -> str:
    """Applies a custom patch format to safely execute file operations.
    
    The patch string can contain multiple blocks enclosed by `*** Begin Patch` and `*** End Patch`.
    Supported Actions: Add, Delete, Move, Modify.
    
    Format example for Modify:
    *** Begin Patch
    Action: Modify
    File: path/to/file.py
    
    <<<<
    old content
    ====
    new content
    >>>>
    *** End Patch
    
    Format example for Add:
    *** Begin Patch
    Action: Add
    File: path/to/newfile.py
    
    <content here>
    *** End Patch
    
    Format example for Move:
    *** Begin Patch
    Action: Move
    File: old/path.py
    Destination: new/path.py
    *** End Patch
    
    Format example for Delete:
    *** Begin Patch
    Action: Delete
    File: path/to/file.py
    *** End Patch
    
    Args:
        patch: The patch string containing the patch blocks.
        
    Returns:
        JSON string indicating success or error.
    """
    try:
        blocks = re.findall(r'\*\*\* Begin Patch(.*?)\*\*\* End Patch', patch, re.DOTALL)
        if not blocks:
            return json.dumps({"status": "error", "message": "No valid patch blocks found."})
        
        operations = []
        for block in blocks:
            block = block.strip()
            lines = block.split('\n')
            action = None
            file_path = None
            destination = None
            content = None
            
            # Parse header
            header_lines = []
            content_lines = []
            parsing_header = True
            
            for line in lines:
                if parsing_header and (line.startswith('Action:') or line.startswith('File:') or line.startswith('Destination:')):
                    header_lines.append(line)
                elif parsing_header and not line.strip():
                    parsing_header = False
                elif not parsing_header:
                    content_lines.append(line)
                elif not (line.startswith('Action:') or line.startswith('File:') or line.startswith('Destination:')):
                    parsing_header = False
                    content_lines.append(line)
                    
            for h in header_lines:
                if h.startswith('Action:'):
                    action = h.split(':', 1)[1].strip().lower()
                elif h.startswith('File:'):
                    file_path = h.split(':', 1)[1].strip()
                elif h.startswith('Destination:'):
                    destination = h.split(':', 1)[1].strip()
                    
            if not action or not file_path:
                return json.dumps({"status": "error", "message": "Missing Action or File in block."})
                
            operations.append({
                "action": action,
                "file": file_path,
                "destination": destination,
                "content": "\n".join(content_lines)
            })
            
        base_dir = os.getcwd()
        
        # Dry run validation
        for op in operations:
            file_path = os.path.abspath(os.path.join(base_dir, op["file"]))
            if not file_path.startswith(base_dir):
                return json.dumps({"status": "error", "message": f"Path outside workspace: {op['file']}"})
                
            if op["action"] == "add":
                if os.path.exists(file_path):
                    return json.dumps({"status": "error", "message": f"File already exists: {op['file']}"})
            elif op["action"] in ["delete", "modify", "move"]:
                if not os.path.exists(file_path):
                    return json.dumps({"status": "error", "message": f"File not found: {op['file']}"})
                    
            if op["action"] == "move":
                dest_path = os.path.abspath(os.path.join(base_dir, op["destination"]))
                if not dest_path.startswith(base_dir):
                    return json.dumps({"status": "error", "message": f"Destination outside workspace: {op['destination']}"})
                if os.path.exists(dest_path):
                    return json.dumps({"status": "error", "message": f"Destination already exists: {op['destination']}"})
                    
        # Apply operations
        results = []
        for op in operations:
            file_path = os.path.abspath(os.path.join(base_dir, op["file"]))
            
            if op["action"] == "add":
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(op["content"])
                results.append(f"Added {op['file']}")
                
            elif op["action"] == "delete":
                os.remove(file_path)
                results.append(f"Deleted {op['file']}")
                
            elif op["action"] == "move":
                dest_path = os.path.abspath(os.path.join(base_dir, op["destination"]))
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                os.rename(file_path, dest_path)
                results.append(f"Moved {op['file']} to {op['destination']}")
                
            elif op["action"] == "modify":
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_text = f.read()
                
                content_block = op["content"]
                if "<<<<" in content_block and "====" in content_block and ">>>>" in content_block:
                    parts = content_block.split("<<<<", 1)[1].split("====", 1)
                    old_text = parts[0]
                    new_text = parts[1].split(">>>>", 1)[0]
                    
                    # Remove leading/trailing newlines specifically for the search/replace block itself
                    # but keep internal whitespace. Usually people put a newline right after <<<<.
                    if old_text.startswith('\n'): old_text = old_text[1:]
                    if old_text.endswith('\n'): old_text = old_text[:-1]
                    if new_text.startswith('\n'): new_text = new_text[1:]
                    if new_text.endswith('\n'): new_text = new_text[:-1]
                    
                    if old_text not in current_text:
                        # Attempt fallback with strict matching
                        return json.dumps({"status": "error", "message": f"Search text not found in {op['file']}"})
                        
                    new_content = current_text.replace(old_text, new_text, 1)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    results.append(f"Modified {op['file']}")
                else:
                    return json.dumps({"status": "error", "message": f"Invalid Modify block format for {op['file']}. Missing <<<<, ====, or >>>>"})
                    
        return json.dumps({"status": "success", "results": results})
        
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
