import argparse
import asyncio
import json
import os
import re
import sys
import yaml
from google.antigravity import Agent

# Import factory modules
from factory.agents import get_researcher_config, get_copywriter_config, get_publisher_config
from factory.utils.validation import clean_json_content, validate_data
from factory.utils.retrieval import retrieve_relevant_units, get_knowledge_unit_by_id

async def run_stage_brief(topic: str, output_file: str):
    print(f"🚀 [Stage 1: Briefing] topic: '{topic}'")
    
    # 1. Retrieve knowledge units
    print("🔍 Scanning knowledge repository...")
    relevant_units = retrieve_relevant_units(topic, limit=3)
    if not relevant_units:
        print("⚠️ Warning: No active, relevant knowledge units found matching the topic.")
        print("Pipeline requires approved, active knowledge units. Please run approve.py first.")
        sys.exit(1)
        
    print(f"✅ Found {len(relevant_units)} relevant knowledge unit(s):")
    for unit in relevant_units:
        print(f" - [{unit['id']}] {unit['title']}")

    knowledge_context_str = json.dumps([
        {
            "id": u["id"],
            "title": u["title"],
            "type": u["type"],
            "tags": u["tags"],
            "content": u["content"]
        } for u in relevant_units
    ], indent=2)

    # 2. Spawning Researcher agent
    researcher_config = get_researcher_config()
    async with Agent(researcher_config) as researcher:
        print("\n🧠 Querying Researcher Agent to compile brief...")
        prompt = (
            f"Retrieved Knowledge Units:\n"
            f"```json\n{knowledge_context_str}\n```\n\n"
            f"Compile a structured Content Brief for: '{topic}'. "
            f"Ground your outline points and takeaways ONLY in the knowledge units provided above."
        )
        
        raw_brief = ""
        response = await researcher.chat(prompt)
        async for token in response:
            raw_brief += token

    cleaned_brief_str = clean_json_content(raw_brief)
    try:
        brief_data = json.loads(cleaned_brief_str)
        is_valid, err_msg = validate_data(brief_data, "content_brief")
        if not is_valid:
            print(f"❌ Brief Validation Failed: {err_msg}")
            sys.exit(1)
            
        # Append status metadata
        brief_data["status"] = "review_pending"
        
        # Save draft brief to disk
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(brief_data, f, indent=2)
            
        print(f"\n✅ Content Brief generated successfully and saved to: {output_file}")
        print("👉 Please review the brief details. Once approved, run the pipeline with `--stage write`.")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Brief as JSON: {e}")
        print("Raw brief structure was:")
        print(raw_brief)
        sys.exit(1)

def slugify(text: str) -> str:
    """Utility to turn titles into clean kebab-case slugs."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text

async def run_stage_write(brief_path: str):
    print(f"🚀 [Stage 2: Writing & Distribution] Loading brief from: {brief_path}")
    if not os.path.exists(brief_path):
        print(f"❌ Brief file not found: {brief_path}")
        sys.exit(1)
        
    with open(brief_path, "r", encoding="utf-8") as f:
        brief_data = json.load(f)

    # Validate brief schema
    is_valid, err_msg = validate_data(brief_data, "content_brief")
    if not is_valid:
        print(f"❌ Brief Schema Validation Failed: {err_msg}")
        sys.exit(1)

    # Verify status
    if brief_data.get("status") == "review_pending":
        print("⚠️ Warning: brief status is 'review_pending'. Writing copy anyway as requested.")

    # Load details of referenced knowledge units
    referenced_ids = set()
    for section in brief_data.get("outline", []):
        for ref_id in section.get("referenced_knowledge_ids", []):
            referenced_ids.add(ref_id)
            
    print(f"📂 Loading details for referenced knowledge IDs: {list(referenced_ids)}...")
    referenced_contents = []
    for ref_id in referenced_ids:
        unit = get_knowledge_unit_by_id(ref_id)
        if unit:
            referenced_contents.append({
                "id": unit["id"],
                "title": unit["title"],
                "content": unit["content"]
            })
        else:
            print(f"⚠️ Warning: Brief referenced knowledge ID '{ref_id}' but it was not found in the local repository.")

    referenced_context_str = json.dumps(referenced_contents, indent=2)

    # 1. Spawn Copywriter Agent to generate raw draft
    writer_config = get_copywriter_config()
    raw_draft = ""
    async with Agent(writer_config) as writer:
        print("\n✍️ Querying Copywriter Agent to draft copy...")
        prompt = (
            f"Validated Content Brief:\n"
            f"```json\n{json.dumps(brief_data, indent=2)}\n```\n\n"
            f"Grounded Knowledge Contents:\n"
            f"```json\n{referenced_context_str}\n```\n\n"
            f"Write the final draft copy. Ensure all statements are strictly aligned with the Grounded Knowledge Contents."
        )
        
        response = await writer.chat(prompt)
        async for token in response:
            raw_draft += token
            sys.stdout.write(token)
            sys.stdout.flush()
        print()

    # 2. Spawn Publisher Agent to package & structure the publication
    print("\n📦 Structuring publication package using Publisher Agent...")
    publisher_config = get_publisher_config()
    raw_pub = ""
    async with Agent(publisher_config) as publisher:
        prompt = (
            f"Original Brief:\n"
            f"```json\n{json.dumps(brief_data, indent=2)}\n```\n\n"
            f"Copywriter Raw Draft:\n"
            f"```markdown\n{raw_draft}\n```\n\n"
            f"Please structure this into a valid Publication JSON object matching the requested schema."
        )
        response = await publisher.chat(prompt)
        async for token in response:
            raw_pub += token

    # Clean and validate publication JSON
    cleaned_pub_str = clean_json_content(raw_pub)
    try:
        pub_data = json.loads(cleaned_pub_str)
        is_valid, err_msg = validate_data(pub_data, "publication")
        if not is_valid:
            print(f"❌ Publication Schema Validation Failed: {err_msg}")
            sys.exit(1)
        print("✅ Publication Schema Validation Succeeded!")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Publication as JSON: {e}")
        print("Raw publication structure was:")
        print(raw_pub)
        sys.exit(1)

    # 3. Export to dist/
    target_channel = pub_data["target_channel"] # blog, faq, page
    dist_dir = os.path.join("dist", f"{target_channel}s")
    os.makedirs(dist_dir, exist_ok=True)

    # Build frontmatter and content body
    meta_to_write = {k: v for k, v in pub_data.items() if k != "content_body"}
    yaml_frontmatter = yaml.safe_dump(meta_to_write, sort_keys=False, default_flow_style=False).strip()
    
    slug = slugify(pub_data["title"])
    output_file = os.path.join(dist_dir, f"{slug}.md")
    
    file_content = f"---\n{yaml_frontmatter}\n---\n\n{pub_data['content_body'].strip()}\n"
    with open(output_file, "w", encoding="utf-8") as out_f:
        out_f.write(file_content)

    print(f"\n🎉 Grounded Content published successfully to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Aether Content Factory Orchestrator CLI.")
    parser.add_argument("--stage", choices=["brief", "write"], required=True, help="Execution stage to run.")
    parser.add_argument("--topic", default="AI Design workflows", help="The topic for Stage 1 (Briefing).")
    parser.add_argument("--output-brief", default="content/briefs/draft_brief.json", help="Path to write the brief draft.")
    parser.add_argument("--brief", default="content/briefs/draft_brief.json", help="Path to input brief file for Stage 2.")
    
    args = parser.parse_args()
    
    if args.stage == "brief":
        asyncio.run(run_stage_brief(args.topic, args.output_brief))
    elif args.stage == "write":
        asyncio.run(run_stage_write(args.brief))

if __name__ == "__main__":
    main()
