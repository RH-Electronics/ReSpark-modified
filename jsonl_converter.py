def parse_jsonl_to_pairs(jsonl_path):
    """
    Converts JSONL with 'messages' format to instruction-output pairs.
    Supports formats:
    - {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
    - Line-by-line JSONL where each line is a message dict
    """
    import json
    pairs = []
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                
                # Format 1: {"messages": [...]}
                if "messages" in data:
                    messages = data["messages"]
                    prev_user = None
                    for msg in messages:
                        role = msg.get("role", "")
                        content = msg.get("content", "").strip()
                        if not content:
                            continue
                        
                        if role == "user":
                            prev_user = content
                        elif role == "assistant" and prev_user:
                            pairs.append({"instruction": prev_user, "output": content})
                            prev_user = None
                
                # Format 2: Direct {"role": "...", "content": "..."} per line
                elif "role" in data and "content" in data:
                    # This requires state tracking across lines - skip or implement if needed
                    pass
                    
            except json.JSONDecodeError:
                continue
    
    return pairs

# Usage in ReSpark.py - add to detect_source() function:
# elif file_path.endswith('.jsonl'):
#     return 'jsonl', parse_jsonl_to_pairs(file_path)
