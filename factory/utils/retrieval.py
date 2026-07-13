import os
import re
from typing import Any, Dict, List, Optional
from factory.utils.validation import parse_markdown_frontmatter

def load_all_knowledge_units(base_dir: str = "knowledge") -> List[Dict[str, Any]]:
    """Recursively loads all knowledge units from the knowledge directory."""
    units = []
    if not os.path.exists(base_dir):
        return units

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    metadata, content = parse_markdown_frontmatter(file_path)
                    if metadata and "id" in metadata:
                        # Append the parsed markdown body back to the metadata dict as content
                        unit = metadata.copy()
                        unit["content"] = content
                        units.append(unit)
                except Exception as e:
                    print(f"⚠️ Warning: failed to parse knowledge unit at {file_path}: {e}")
    return units

def retrieve_relevant_units(query_topic: str, base_dir: str = "knowledge", limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieves relevant knowledge units matching the query topic.
    
    Performs basic keyword token overlap scoring against ID, title, content, and tags.
    """
    units = load_all_knowledge_units(base_dir)
    if not units:
        return []

    # Clean query into tokens
    query_tokens = set(re.findall(r"\w+", query_topic.lower()))
    scored_units = []

    for unit in units:
        score = 0
        
        # 1. Check ID & title match (high weight)
        title_tokens = set(re.findall(r"\w+", unit.get("title", "").lower()))
        id_tokens = set(re.findall(r"\w+", unit.get("id", "").lower()))
        score += len(query_tokens.intersection(title_tokens)) * 3
        score += len(query_tokens.intersection(id_tokens)) * 2

        # 2. Check tag match (high weight)
        tags = [str(t).lower() for t in unit.get("tags", [])]
        score += len(query_tokens.intersection(tags)) * 4

        # 3. Check content match (lower weight)
        content_tokens = set(re.findall(r"\w+", unit.get("content", "").lower()))
        score += len(query_tokens.intersection(content_tokens)) * 1

        if score > 0:
            scored_units.append((score, unit))

    # Sort by score descending and return units up to the limit
    scored_units.sort(key=lambda x: x[0], reverse=True)
    return [unit for _, unit in scored_units[:limit]]

def get_knowledge_unit_by_id(unit_id: str, base_dir: str = "knowledge") -> Optional[Dict[str, Any]]:
    """Finds a specific knowledge unit by its unique ID."""
    units = load_all_knowledge_units(base_dir)
    for unit in units:
        if unit.get("id") == unit_id:
            return unit
    return None

def detect_similar_unit(new_unit: Dict[str, Any], base_dir: str = "knowledge") -> Optional[Dict[str, Any]]:
    """Detects if a similar knowledge unit already exists in active storage.
    
    Matches by exact ID, or a high token overlap (> 70%) in title.
    """
    new_id = new_unit.get("id")
    new_title = new_unit.get("title", "")
    new_title_tokens = set(re.findall(r"\w+", new_title.lower()))
    
    units = load_all_knowledge_units(base_dir)
    for unit in units:
        # Ignore draft folder items to check only active storage
        # Load all knowledge units defaults to scanning the base_dir.
        # But wait, we should skip units that are still drafts
        if unit.get("status") == "review_pending":
            continue
            
        if unit.get("id") == new_id:
            return unit
            
        # Check title similarity
        existing_title = unit.get("title", "")
        ex_title_tokens = set(re.findall(r"\w+", existing_title.lower()))
        if not new_title_tokens or not ex_title_tokens:
            continue
            
        overlap = len(new_title_tokens.intersection(ex_title_tokens))
        union = len(new_title_tokens.union(ex_title_tokens))
        similarity = overlap / union
        
        if similarity >= 0.70:
            return unit
            
    return None
