import os
import json
import uuid
import datetime
import re

SESSION_DIR = os.path.abspath("./.sessions")

DEFAULT_WORKFLOW_STATE = {
    "current_stage": "explore",
    "create_data": {
        "title": "",
        "category": "Feature",
        "goal": "",
        "context": ""
    },
    "spec_data": {
        "sections": [],
        "open_questions": []
    },
    "develop_data": {
        "workflow_steps": [],
        "file_tree": [],
        "code_snippets": [],
        "open_questions": []
    },
    "testing_data": {
        "test_steps": [],
        "env_vars": {},
        "test_runs": [],
        "remediation_instructions": "",
        "regression_baseline": []
    },
    "completed_data": {
        "summary_items": [],
        "created_files": [],
        "verification_results": []
    },
    "references": []
}

def ensure_session_dir():
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR, exist_ok=True)

def write_markdown_summary(session_data):
    ensure_session_dir()
    
    # Resolve date (use created_at or current date)
    created_at = session_data.get("created_at") or datetime.datetime.utcnow().isoformat()
    date_str = created_at[:10]
    
    # Resolve title (fallback to first conversation)
    first_msg = ""
    for msg in session_data.get("chat_history", []):
        if msg.get("role") == "user":
            first_msg = msg.get("content", "")
            break
            
    title = session_data.get("title")
    if (not title or title in ["New Explore Task", "Untitled Session"]) and first_msg:
        title = first_msg[:40].strip()
        title = " ".join(title.split())
        
    if not title:
        title = "Untitled_Session"
        
    # Sanitize title for filename
    safe_title = re.sub(r'[^\w\s-]', '', title).strip()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)
    if not safe_title:
        safe_title = "session"
        
    filename = f"{date_str}_{safe_title}.md"
    filepath = os.path.join(SESSION_DIR, filename)
    
    # Remove old md file if the filename has changed
    old_md_filename = session_data.get("md_filename_saved")
    if old_md_filename and old_md_filename != filename:
        old_filepath = os.path.join(SESSION_DIR, old_md_filename)
        if os.path.exists(old_filepath):
            try:
                os.remove(old_filepath)
            except Exception:
                pass
                
    session_data["md_filename_saved"] = filename
    
    # Generate markdown content
    lines = []
    lines.append(f"# Session: {title}")
    lines.append(f"- **Session ID**: `{session_data.get('session_id')}`")
    lines.append(f"- **Created At**: {session_data.get('created_at')}")
    lines.append(f"- **Last Updated**: {session_data.get('updated_at')}")
    lines.append(f"- **Current Stage**: `{session_data.get('current_stage', 'explore')}`")
    lines.append("")
    
    summary = session_data.get("summary")
    if summary:
        lines.append("## Executive Summary")
        lines.append(summary)
        lines.append("")
        
    state = session_data.get("state", {})
    create_data = state.get("create_data", {})
    if create_data.get("title"):
        lines.append("## Task Details")
        lines.append(f"- **Title**: {create_data.get('title')}")
        lines.append(f"- **Category**: {create_data.get('category')}")
        lines.append(f"- **Goal**: {create_data.get('goal')}")
        lines.append(f"- **Context**: {create_data.get('context')}")
        lines.append("")
        
    chat_history = session_data.get("chat_history", [])
    if chat_history:
        lines.append("## Conversation History")
        for msg in chat_history:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            ts_str = f" ({timestamp})" if timestamp else ""
            lines.append(f"### {role}{ts_str}")
            lines.append(content)
            lines.append("")
            
    markdown_content = "\n".join(lines)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        return True
    except Exception as e:
        print(f"Error writing markdown summary: {e}")
        return False

def enforce_session_limit():
    ensure_session_dir()
    sessions = []
    for filename in os.listdir(SESSION_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(SESSION_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "updated_at": data.get("updated_at") or "",
                        "md_filename_saved": data.get("md_filename_saved"),
                        "filepath": filepath
                    })
            except Exception:
                pass
    sessions.sort(key=lambda x: x.get("updated_at") or "")
    
    while len(sessions) >= 20:
        oldest = sessions.pop(0)
        try:
            if os.path.exists(oldest["filepath"]):
                os.remove(oldest["filepath"])
            
            md_filename = oldest.get("md_filename_saved")
            if md_filename:
                md_path = os.path.join(SESSION_DIR, md_filename)
                if os.path.exists(md_path):
                    os.remove(md_path)
        except Exception as e:
            print(f"Error enforcing session limit: {e}")

def list_sessions():
    ensure_session_dir()
    sessions = []
    for filename in os.listdir(SESSION_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(SESSION_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append({
                        "session_id": data.get("session_id"),
                        "title": data.get("title") or "Untitled Session",
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "current_stage": data.get("current_stage", "explore")
                    })
            except Exception as e:
                print(f"Error reading session file {filename}: {e}")
    sessions.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return sessions

def load_session(session_id):
    ensure_session_dir()
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
    
    now = datetime.datetime.utcnow().isoformat() + "Z"
    return {
        "session_id": session_id,
        "title": "New Explore Task",
        "created_at": now,
        "updated_at": now,
        "summary": "",
        "current_stage": "explore",
        "state": json.loads(json.dumps(DEFAULT_WORKFLOW_STATE)),
        "chat_history": []
    }

def save_session(session_id, session_data):
    ensure_session_dir()
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    
    state = session_data.get("state", {})
    create_data = state.get("create_data", {})
    if create_data.get("title"):
        session_data["title"] = create_data.get("title")
        
    session_data["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    
    write_markdown_summary(session_data)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving session {session_id}: {e}")
        return False

def create_session(title=None):
    enforce_session_limit()
    ensure_session_dir()
    session_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow().isoformat() + "Z"
    new_session = {
        "session_id": session_id,
        "title": title or "New Explore Task",
        "created_at": now,
        "updated_at": now,
        "summary": "",
        "current_stage": "explore",
        "state": json.loads(json.dumps(DEFAULT_WORKFLOW_STATE)),
        "chat_history": []
    }
    save_session(session_id, new_session)
    return new_session

def delete_session(session_id):
    ensure_session_dir()
    # Read session JSON first to identify the markdown file
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                md_filename = data.get("md_filename_saved")
                if md_filename:
                    md_path = os.path.join(SESSION_DIR, md_filename)
                    if os.path.exists(md_path):
                        os.remove(md_path)
            os.remove(filepath)
            return True
        except Exception as e:
            print(f"Error deleting session file {session_id}: {e}")
    return False

ACTIVE_SESSION_ID = None

def get_active_session_id():
    global ACTIVE_SESSION_ID
    if ACTIVE_SESSION_ID is None:
        sessions = list_sessions()
        if sessions:
            ACTIVE_SESSION_ID = sessions[0]["session_id"]
        else:
            new_sess = create_session()
            ACTIVE_SESSION_ID = new_sess["session_id"]
    return ACTIVE_SESSION_ID

def set_active_session_id(session_id):
    global ACTIVE_SESSION_ID
    ACTIVE_SESSION_ID = session_id
