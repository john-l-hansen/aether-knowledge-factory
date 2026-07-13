import json
import os
import re
from typing import Any, Dict, Optional, Tuple
import jsonschema
import yaml

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Loads a JSON schema from the factory/schemas directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "schemas", f"{schema_name}.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_json_content(content: str) -> str:
    """Strips markdown code fences (like ```json ... ```) from JSON strings."""
    content = content.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return content

def validate_data(data: Dict[str, Any], schema_name: str) -> Tuple[bool, Optional[str]]:
    """Validates a dictionary data structure against a schema file."""
    try:
        schema = load_schema(schema_name)
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, f"Validation Error: {e.message} (path: {list(e.path)})"
    except Exception as e:
        return False, f"Unexpected validation error: {str(e)}"

def parse_markdown_frontmatter(file_path: str) -> Tuple[Dict[str, Any], str]:
    """Parses a Markdown file containing YAML frontmatter.
    
    Returns a tuple containing the parsed metadata dictionary and the markdown body.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Matches YAML frontmatter block starting and ending with ---
    match = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$", content)
    if match:
        yaml_block = match.group(1)
        markdown_body = match.group(2)
        metadata = yaml.safe_load(yaml_block) or {}
        return metadata, markdown_body
    
    return {}, content
