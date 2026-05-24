import datetime

class NoteClassifier:
    def __init__(self):
        pass

    def classify_and_format(self, raw_content, user_instruction=""):
        """
        分析隨手記內容並生成標準的 Markdown 格式與 YAML 屬性
        """
        category = "Reference"
        status = "todo"
        
        content_lower = raw_content.lower()
        if "待辦" in content_lower or "任務" in content_lower or "完成" in content_lower:
            category = "Action"
            status = "active"
        elif "會議" in content_lower or "地點" in content_lower or "討論" in content_lower:
            category = "Context"
            status = "active"
            
        if "#action" in user_instruction:
            category = "Action"
        elif "#reference" in user_instruction:
            category = "Reference"
        elif "#context" in user_instruction:
            category = "Context"

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = raw_content.split("\n")[0][:20] if raw_content else "未命名筆記"
        
        yaml_properties = []
        yaml_properties.append("---")
        yaml_properties.append(f"title: {title}")
        yaml_properties.append(f"created: {now_str}")
        yaml_properties.append(f"updated: {now_str}")
        yaml_properties.append(f"tags: [{category.lower()}]")
        yaml_properties.append("aliases: []")
        yaml_properties.append(f"status: {status}")
        yaml_properties.append(f"type: {category}")
        yaml_properties.append("---")
        
        yaml_header = "\n".join(yaml_properties)
        formatted_markdown = f"{yaml_header}\n\n{raw_content}"
        
        return category, title, formatted_markdown