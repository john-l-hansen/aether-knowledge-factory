import asyncio
import json
import sys
from google.antigravity import Agent

# Import modules from our factory package
from factory.agents import get_researcher_config, get_copywriter_config
from factory.utils.validation import clean_json_content, validate_data

async def run_content_pipeline(topic: str):
    print(f"🚀 Initializing Aether Content Factory for topic: '{topic}'...\n")

    # 1. Spawn the Researcher Agent to gather and structure the brief
    researcher_config = get_researcher_config()
    
    async with Agent(researcher_config) as researcher:
        print("🔍 Step 1: Researching topic & compiling structured brief...")
        raw_brief = ""
        response = await researcher.chat(f"Research and compile a structured Content Brief for: {topic}")
        async for token in response:
            raw_brief += token
        
    print("\n--- Raw Brief Received ---")
    print(raw_brief[:500] + "\n...[Brief Truncated for Output]\n")

    # Clean and validate the brief
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

    # 2. Spawn the Copywriter Agent to write the content based on the validated brief
    writer_config = get_copywriter_config()

    async with Agent(writer_config) as writer:
        print("\n✍️ Step 2: Drafting content using validated brief...")
        draft = ""
        response = await writer.chat(
            f"Using the following validated JSON content brief, write the main copy/draft:\n\n"
            f"{json.dumps(brief_data, indent=2)}"
        )
        async for token in response:
            draft += token
            sys.stdout.write(token)
            sys.stdout.flush()
        print()

    print("\n✅ Content pipeline run completed successfully!")

if __name__ == "__main__":
    # Use standard library event loop
    topic = "The Future of AI in Creative Design"
    asyncio.run(run_content_pipeline(topic))
