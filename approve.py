import argparse
import os
import sys
import yaml
from factory.utils.validation import parse_markdown_frontmatter, validate_data

def approve_unit(file_path: str) -> bool:
    """Validates, updates status to active, and moves the unit to its permanent folder."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
        
    metadata, content = parse_markdown_frontmatter(file_path)
    if not metadata or "id" not in metadata:
        print(f"❌ Invalid markdown frontmatter in {file_path}")
        return False
        
    # Promote status to active
    metadata["status"] = "active"
    
    # Run full schema validation
    unit_data = metadata.copy()
    unit_data["content"] = content
    is_valid, err_msg = validate_data(unit_data, "knowledge_unit")
    if not is_valid:
        print(f"❌ Schema validation failed for '{metadata['id']}': {err_msg}")
        return False

    # Determine target category folder
    unit_type = metadata["type"]
    target_dir = os.path.join("knowledge", f"{unit_type}s")
    os.makedirs(target_dir, exist_ok=True)
    
    target_file = os.path.join(target_dir, f"{metadata['id']}.md")
    
    # Re-dump YAML frontmatter + content
    yaml_str = yaml.safe_dump(metadata, sort_keys=False, default_flow_style=False).strip()
    file_content = f"---\n{yaml_str}\n---\n\n{content.strip()}\n"
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(file_content)
        
    # Clean up draft file
    os.remove(file_path)
    print(f"✅ Approved and Promoted: {target_file}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Aether Knowledge Factory - Human Approval CLI Utility.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", help="The ID of the draft knowledge unit to approve.")
    group.add_argument("--all", action="store_true", help="Approve all pending drafts in knowledge/drafts.")
    args = parser.parse_args()

    draft_dir = os.path.join("knowledge", "drafts")
    if not os.path.exists(draft_dir) or not os.listdir(draft_dir):
        print("📂 No pending drafts found in knowledge/drafts.")
        sys.exit(0)

    if args.id:
        file_path = os.path.join(draft_dir, f"{args.id}.md")
        if not approve_unit(file_path):
            sys.exit(1)
    elif args.all:
        print(f"🔄 Commencing approval for all files in {draft_dir}...")
        files = [f for f in os.listdir(draft_dir) if f.endswith(".md")]
        success = 0
        for f in files:
            file_path = os.path.join(draft_dir, f)
            if approve_unit(file_path):
                success += 1
        print(f"\n🎉 Approval run complete. Successfully approved {success}/{len(files)} draft units.")

if __name__ == "__main__":
    main()
