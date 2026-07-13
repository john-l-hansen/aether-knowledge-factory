import json
import os
import re
from typing import Any, Dict, Optional, Tuple
import jsonschema

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Loads a JSON schema from the factory/schemas directory."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, "schemas", f"{schema_name}.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_json_content(content: str) -> str:
    """Strips markdown code fences (like ```json ... ```) from JSON strings."""
    content = content.strip()
    # Strip markdown block if present
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
