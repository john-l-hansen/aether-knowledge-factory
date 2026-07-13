import argparse
import asyncio
import json
import os
import sys
from google.antigravity import Agent

# Import factory modules
from factory.agents import get_researcher_config, get_copywriter_config
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

async def run_stage_write(brief_path: str):
    print(f"🚀 [Stage 2: Writing] Loading brief from: {brief_path}")
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

    # Verify status (warn if still review_pending, but allow continuing if user runs the command)
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

    # Spawn Copywriter Agent
    writer_config = get_copywriter_config()
    async with Agent(writer_config) as writer:
        print("\n✍️ Querying Copywriter Agent to draft copy...")
        prompt = (
            f"Validated Content Brief:\n"
            f"```json\n{json.dumps(brief_data, indent=2)}\n```\n\n"
            f"Grounded Knowledge Contents:\n"
            f"```json\n{referenced_context_str}\n```\n\n"
            f"Write the final draft copy. Ensure all statements are strictly aligned with the Grounded Knowledge Contents."
        )
        
        draft = ""
        response = await writer.chat(prompt)
        async for token in response:
            draft += token
            sys.stdout.write(token)
            sys.stdout.flush()
        print()

    print("\n✅ Grounded Content writing completed successfully!")

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
