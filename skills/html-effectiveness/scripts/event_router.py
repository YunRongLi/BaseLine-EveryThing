# SPDX-License-Identifier: GPL-2.0
# Copyright (c) 2026 Martin Li. All rights reserved.

import json

class LLMAgentEventRouter:
    """
    Modular event router for classification of LLM Agent nested JSON events.
    Enforces a strict 3-layered routing system:
    1. Permission Asked Checks (event.type == permission.asked)
    2. Message Part Updates (event.type == message.part.updated)
    3. Low-Latency Streaming Delta Parsing (event.type == message.part.delta)
    """
    def __init__(self):
        pass

    def route_event(self, event_payload: dict) -> dict:
        """
        Routes the parsed JSON event dictionary based on the 3-layered protocol.
        
        Args:
            event_payload: Pre-parsed dictionary representing the structured event.
            
        Returns:
            Dictionary containing the classification outcome and metadata.
        """
        try:
            event_type = event_payload.get("type")
            if not event_type:
                return {"status": "ignored", "reason": "Missing type in event payload"}

            # Layer 1: Permission asked checks
            if event_type == "permission.asked":
                permission_data = event_payload.get("permission", {})
                perm_type = permission_data.get("permission")
                target = permission_data.get("target", "")
                
                if perm_type in ["edit", "bash"]:
                    return {
                        "status": "requires_confirmation",
                        "permission": perm_type,
                        "target": target,
                        "message": f"High-risk operation requested: {perm_type} on target: {target}."
                    }
                return {
                    "status": "approved",
                    "permission": perm_type,
                    "target": target
                }

            # Layer 2: Part updates (Tooling / Text)
            elif event_type == "message.part.updated":
                part = event_payload.get("part", {})
                part_type = part.get("type")
                
                if part_type == "tool":
                    state = part.get("state", {})
                    status = state.get("status")
                    detail = state.get("detail", "")
                    
                    status_map = {
                        "pending": "Initializing tool execution...",
                        "running": f"Executing tool: {detail}",
                        "completed": "Tool run successfully.",
                        "error": f"Tool execution failed: {detail}"
                    }
                    msg = status_map.get(status, f"Tool status: {status}")
                    return {
                        "status": "processed",
                        "type": "tool",
                        "tool_status": status,
                        "message": msg
                    }
                elif part_type == "text":
                    text_val = part.get("text", "")
                    return {
                        "status": "processed",
                        "type": "text",
                        "content": text_val
                    }

            # Layer 3: Streaming Delta Logic
            elif event_type == "message.part.delta":
                props = event_payload.get("props", {})
                field = props.get("field")
                delta_val = props.get("delta", "")
                
                if field in ["text", "reasoning"]:
                    return {
                        "status": "stream",
                        "field": field,
                        "delta": delta_val
                    }

            return {"status": "unhandled", "type": event_type}

        except Exception as e:
            return {"status": "error", "message": str(e)}
