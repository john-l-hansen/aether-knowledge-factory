import argparse
import asyncio
import json
import os
import sys
import yaml
from google.antigravity import Agent

# Import factory modules
from factory.agents import get_curator_config, get_merger_config
from factory.utils.validation import clean_json_content, validate_data
from factory.utils.retrieval import detect_similar_unit

async def run_ingestion(source_path: str):
    if not os.path.exists(source_path):
        print(f"❌ Source file not found: {source_path}")
        sys.exit(1)
        
    print(f"📖 Reading raw input from: {source_path}...")
    with open(source_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # 1. Spin up curator agent
    curator_config = get_curator_config()
    print("🧠 Spawning Curator Agent to extract structured knowledge units...")
    
    async with Agent(curator_config) as agent:
        response = await agent.chat(
            f"Analyze the following raw input and extract all knowledge units (concepts, insights, facts):\n\n"
            f"{raw_text}"
        )
        raw_output = ""
        async for token in response:
            raw_output += token

    print("\n--- Raw Curator Response ---")
    print(raw_output[:500] + "\n...[Output Truncated]")
    
    cleaned_json = clean_json_content(raw_output)
    try:
        extracted_units = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse output as JSON array: {e}")
        print("Raw output received was:")
        print(raw_output)
        sys.exit(1)

    if not isinstance(extracted_units, list):
        print(f"❌ Expected a JSON array, got: {type(extracted_units).__name__}")
        sys.exit(1)

    print(f"\n📂 Processing {len(extracted_units)} knowledge units...")
    
    success_count = 0
    for idx, unit in enumerate(extracted_units):
        # Check for similarity with existing units
        existing_unit = detect_similar_unit(unit)
        
        if existing_unit:
            print(f"\n🔄 Conflict Detected: Proposed unit [{unit.get('id')}] overlaps with existing active unit [{existing_unit.get('id')}]!")
            print("🧠 Spawning Merger Agent to consolidate concepts...")
            
            merger_config = get_merger_config()
            async with Agent(merger_config) as merger:
                prompt = (
                    f"Existing Active Unit:\n"
                    f"```json\n{json.dumps(existing_unit, indent=2)}\n```\n\n"
                    f"Newly Proposed Unit:\n"
                    f"```json\n{json.dumps(unit, indent=2)}\n```\n\n"
                    f"Merge these two units into a single consolidated JSON unit. Eliminate redundancies."
                )
                
                raw_merge = ""
                response = await merger.chat(prompt)
                async for token in response:
                    raw_merge += token
                    
            cleaned_merge = clean_json_content(raw_merge)
            try:
                unit = json.loads(cleaned_merge)
                print("✅ Successfully merged units!")
            except json.JSONDecodeError as e:
                print(f"⚠️ Warning: Failed to parse merged unit as JSON: {e}. Defaulting to proposed unit.")
                
        # Inject status field
        unit["status"] = "review_pending"

        # Validate against the knowledge_unit schema
        is_valid, err_msg = validate_data(unit, "knowledge_unit")
        if not is_valid:
            print(f"⚠️ Skip Unit [{idx}]: {err_msg}")
            continue

        # Force save to drafts folder for Human-in-the-Loop review
        target_dir = os.path.join("knowledge", "drafts")
        os.makedirs(target_dir, exist_ok=True)

        # Build file content: YAML frontmatter + markdown content
        meta_to_write = {k: v for k, v in unit.items() if k != "content"}
        yaml_frontmatter = yaml.safe_dump(meta_to_write, sort_keys=False, default_flow_style=False).strip()
        
        file_name = f"{unit['id']}.md"
        file_path = os.path.join(target_dir, file_name)
        
        file_content = f"---\n{yaml_frontmatter}\n---\n\n{unit['content'].strip()}\n"
        with open(file_path, "w", encoding="utf-8") as out_f:
            out_f.write(file_content)
            
        print(f"✅ Saved Draft: {file_path}")
        success_count += 1

    print(f"\n🎉 Ingestion completed. Successfully processed {success_count}/{len(extracted_units)} units.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest raw text into structured knowledge units.")
    parser.add_argument("--source", required=True, help="Path to raw text source file.")
    args = parser.parse_args()

    asyncio.run(run_ingestion(args.source))
