import argparse
import json
import os
import sys
import requests
from factory.utils.validation import parse_markdown_frontmatter, convert_markdown_to_html

def load_env():
    """Loads a local .env file if it exists."""
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

def publish_to_webflow(file_path: str, dry_run: bool = True):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
        
    print(f"📖 Reading publication asset: {file_path}...")
    metadata, content = parse_markdown_frontmatter(file_path)
    
    if not metadata or "title" not in metadata:
        print("❌ Invalid publication asset. Missing required frontmatter title.")
        sys.exit(1)

    # Convert markdown body to HTML for Webflow Rich Text field
    html_body = convert_markdown_to_html(content)
    
    # Get slug from filename
    slug = os.path.splitext(os.path.basename(file_path))[0]
    
    # Build Webflow Collection Item Payload (Webflow API v2 format)
    payload = {
        "isArchived": False,
        "isDraft": False,
        "fieldData": {
            "name": metadata["title"],
            "slug": slug,
            "post-body": html_body,
            "summary": metadata.get("excerpt", "")
        }
    }

    if dry_run:
        print("\n🔍 --- Webflow Publish DRY RUN ---")
        print(f"Target URL: https://api.webflow.com/v2/collections/MOCK_COLLECTION_ID/items")
        print("Headers: { 'Authorization': 'Bearer MOCK_TOKEN', 'Content-Type': 'application/json' }")
        print("Payload:")
        print(json.dumps(payload, indent=2))
        print("\n✅ Dry run completed successfully. (Pass --publish to push live)")
        return

    # Real publishing flow
    load_env()
    token = os.environ.get("WEBFLOW_ACCESS_TOKEN")
    collection_id = os.environ.get("WEBFLOW_COLLECTION_ID")

    if not token or not collection_id:
        print("❌ Error: WEBFLOW_ACCESS_TOKEN and WEBFLOW_COLLECTION_ID environment variables must be set.")
        print("Create a .env file or export them in your terminal before running with --publish.")
        sys.exit(1)

    url = f"https://api.webflow.com/v2/collections/{collection_id}/items"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"🚀 Pushing item to Webflow collection: {collection_id}...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code in [200, 201, 202]:
            res_data = response.json()
            print(f"🎉 Successfully published to Webflow! Item ID: {res_data.get('id')}")
        else:
            print(f"❌ Failed to publish. Webflow API status code: {response.status_code}")
            print(response.text)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected request error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish dist publication assets directly to Webflow CMS.")
    parser.add_argument("--file", required=True, help="Path to the publication markdown file under dist/.")
    parser.add_argument("--publish", action="store_true", help="Perform actual API request to Webflow CMS.")
    args = parser.parse_args()

    # Dry-run is default unless --publish is explicitly flag-passed
    dry_run_active = not args.publish
    publish_to_webflow(args.file, dry_run=dry_run_active)
