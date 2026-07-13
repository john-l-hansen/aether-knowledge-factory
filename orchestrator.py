import asyncio
import json
import sys
from google.antigravity import Agent

# Import factory modules
from factory.agents import get_researcher_config, get_copywriter_config
from factory.utils.validation import clean_json_content, validate_data
from factory.utils.retrieval import retrieve_relevant_units, get_knowledge_unit_by_id

async def run_content_pipeline(topic: str):
    print(f"🚀 Initializing Aether Content Factory for topic: '{topic}'...\n")

    # 1. Retrieve relevant knowledge units from our database
    print("🔍 Step 1: Querying local knowledge repository...")
    relevant_units = retrieve_relevant_units(topic, limit=3)
    
    if not relevant_units:
        print("⚠️ Warning: No relevant knowledge units found matching the topic.")
        print("Pipeline requires curated knowledge to ground the research. Please run ingest.py first.")
        sys.exit(1)
        
    print(f"✅ Found {len(relevant_units)} relevant knowledge unit(s):")
    for unit in relevant_units:
        print(f" - [{unit['id']}] {unit['title']} (Confidence: {unit['confidence']})")
    print()

    # Format the knowledge units to inject into the researcher prompt
    knowledge_context_str = json.dumps([
        {
            "id": u["id"],
            "title": u["title"],
            "type": u["type"],
            "tags": u["tags"],
            "content": u["content"]
        } for u in relevant_units
    ], indent=2)

    # 2. Spawn the Researcher Agent to compile a grounded content brief
    researcher_config = get_researcher_config()
    async with Agent(researcher_config) as researcher:
        print("🧠 Step 2: Compiling grounded Content Brief...")
        
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
        
    print("\n--- Raw Brief Received ---")
    print(raw_brief[:500] + "\n...[Brief Truncated for Output]\n")

    # Clean and validate the brief structure
    cleaned_brief_str = clean_json_content(raw_brief)
    try:
        brief_data = json.loads(cleaned_brief_str)
        is_valid, err_msg = validate_data(brief_data, "content_brief")
        if not is_valid:
            print(f"❌ Brief Validation Failed: {err_msg}")
            sys.exit(1)
        print("✅ Brief Schema Validation Succeeded!")
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Brief as JSON: {e}")
        print("Raw brief structure was:")
        print(raw_brief)
        sys.exit(1)

    # 3. Gather full details of all referenced knowledge units specified in the brief
    referenced_ids = set()
    for section in brief_data.get("outline", []):
        for ref_id in section.get("referenced_knowledge_ids", []):
            referenced_ids.add(ref_id)
            
    print(f"\n📂 Loading detailed contents for referenced knowledge IDs: {list(referenced_ids)}...")
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

    # 4. Spawn the Copywriter Agent to write the grounded draft
    writer_config = get_copywriter_config()
    async with Agent(writer_config) as writer:
        print("\n✍️ Step 4: Drafting content using validated brief and referenced knowledge...")
        
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

    print("\n✅ Grounded Content pipeline run completed successfully!")

if __name__ == "__main__":
    topic = "AI Design workflows"
    asyncio.run(run_content_pipeline(topic))
