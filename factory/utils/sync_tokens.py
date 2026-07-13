import json
import os

def clean_css_name(name: str) -> str:
    """Converts a Figma variable path into a valid CSS variable name.
    
    Example: 'primitive/color/neutral/950' -> '--primitive-color-neutral-950'
    """
    cleaned = name.lower().replace("/", "-").replace(" ", "-").strip()
    return f"--{cleaned}"

def sync():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tokens_json_path = os.path.join(base_dir, "factory", "schemas", "design_tokens.json")
    tokens_css_path = os.path.join(base_dir, "ui", "design_tokens.css")

    if not os.path.exists(tokens_json_path):
        print(f"❌ Error: design_tokens.json not found at {tokens_json_path}")
        return

    print(f"📖 Reading design tokens from: {tokens_json_path}")
    with open(tokens_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    variables = data.get("variables", {})
    if not variables:
        print("⚠️ Warning: No variables found in design_tokens.json")
        return

    print("🎨 Formatting CSS Custom Properties...")
    css_lines = [
        "/* Generated Design System Custom Properties from Figma Library */",
        ":root {"
    ]

    for key, value in variables.items():
        css_name = clean_css_name(key)
        css_lines.append(f"  {css_name}: {value};")
    
    css_lines.append("}")
    
    css_content = "\n".join(css_lines) + "\n"
    
    with open(tokens_css_path, "w", encoding="utf-8") as out_f:
        out_f.write(css_content)

    print(f"✅ Design System variables successfully synced to: {tokens_css_path}")

if __name__ == "__main__":
    sync()
