import argparse
import json
import os
import subprocess
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer
from factory.utils.retrieval import load_all_knowledge_units
from approve import approve_unit

class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow CORS for local dev ease
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        # Route static files
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == "/" or path == "":
            self.path = "/ui/index.html"
            return super().do_GET()
        elif path.startswith("/ui/"):
            return super().do_GET()

        # Route APIs
        if path == "/api/knowledge":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            all_units = load_all_knowledge_units("knowledge")
            active_units = [u for u in all_units if u.get("status") == "active"]
            self.wfile.write(json.dumps(active_units).encode("utf-8"))
            return

        elif path == "/api/drafts":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            draft_units = []
            draft_dir = os.path.join("knowledge", "drafts")
            if os.path.exists(draft_dir):
                draft_units = load_all_knowledge_units(draft_dir)
            self.wfile.write(json.dumps(draft_units).encode("utf-8"))
            return

        elif path == "/api/brief":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            brief_file = "content/briefs/draft_brief.json"
            if os.path.exists(brief_file):
                with open(brief_file, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.wfile.write(json.dumps({}).encode("utf-8"))
            return

        elif path == "/api/publications":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            pubs = []
            dist_dir = "dist"
            if os.path.exists(dist_dir):
                for root, _, files in os.walk(dist_dir):
                    for file in files:
                        if file.endswith(".md"):
                            rel_path = os.path.relpath(os.path.join(root, file), os.getcwd())
                            pubs.append({"file": rel_path, "name": file})
            self.wfile.write(json.dumps(pubs).encode("utf-8"))
            return

        # Fallback to standard handler
        return super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        if path == "/api/approve":
            unit_id = query.get("id", [None])[0]
            if not unit_id:
                self.send_json_response(400, {"success": False, "error": "Missing 'id' query parameter."})
                return

            draft_file = os.path.join("knowledge", "drafts", f"{unit_id}.md")
            success = approve_unit(draft_file)
            if success:
                self.send_json_response(200, {"success": True})
            else:
                self.send_json_response(500, {"success": False, "error": "Approval failed. Check logs."})
            return

        elif path == "/api/ingest":
            # Read POST body text
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            try:
                body_json = json.loads(post_data)
                raw_text = body_json.get("text", "")
            except Exception:
                raw_text = post_data

            if not raw_text.strip():
                self.send_json_response(400, {"success": False, "error": "Ingestion raw text is empty."})
                return

            os.makedirs("scratch", exist_ok=True)
            temp_file = "scratch/temp_ingest.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(raw_text)

            print("⚡ Dashboard: Spawning ingest.py pipeline...")
            cmd = [sys.executable, "ingest.py", "--source", temp_file]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.send_json_response(200, {"success": True, "logs": result.stdout})
                else:
                    self.send_json_response(500, {"success": False, "error": result.stderr or result.stdout})
            except Exception as e:
                self.send_json_response(500, {"success": False, "error": f"Subprocess run error: {str(e)}"})
            return

        elif path == "/api/generate":
            topic = query.get("topic", [""])[0]
            if not topic:
                self.send_json_response(400, {"success": False, "error": "Missing 'topic' query parameter."})
                return

            print(f"⚡ Dashboard: Spawning orchestrator briefing for topic: {topic}...")
            cmd = [sys.executable, "orchestrator.py", "--stage", "brief", "--topic", topic]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.send_json_response(200, {"success": True, "logs": result.stdout})
                else:
                    self.send_json_response(500, {"success": False, "error": result.stderr or result.stdout})
            except Exception as e:
                self.send_json_response(500, {"success": False, "error": f"Failed to run briefing: {str(e)}"})
            return

        elif path == "/api/brief/approve":
            brief_file = "content/briefs/draft_brief.json"
            if not os.path.exists(brief_file):
                self.send_json_response(404, {"success": False, "error": "No draft brief found to approve."})
                return

            try:
                with open(brief_file, "r", encoding="utf-8") as f:
                    brief_data = json.load(f)
                
                # Update status
                brief_data["status"] = "approved"
                
                with open(brief_file, "w", encoding="utf-8") as f:
                    json.dump(brief_data, f, indent=2)
                self.send_json_response(200, {"success": True})
            except Exception as e:
                self.send_json_response(500, {"success": False, "error": f"Failed to approve brief: {str(e)}"})
            return

        elif path == "/api/write":
            print("⚡ Dashboard: Spawning orchestrator copywriting stage...")
            cmd = [sys.executable, "orchestrator.py", "--stage", "write"]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
                if result.returncode == 0:
                    self.send_json_response(200, {"success": True, "logs": result.stdout})
                else:
                    self.send_json_response(500, {"success": False, "error": result.stderr or result.stdout})
            except Exception as e:
                self.send_json_response(500, {"success": False, "error": f"Failed to run copywriter: {str(e)}"})
            return

        elif path == "/api/publish":
            file_path = query.get("file", [None])[0]
            if not file_path:
                self.send_json_response(400, {"success": False, "error": "Missing 'file' parameter."})
                return

            print(f"⚡ Dashboard: Spawning publish_webflow.py for file: {file_path}...")
            cmd = [sys.executable, "publish_webflow.py", "--file", file_path, "--publish"]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.send_json_response(200, {"success": True, "logs": result.stdout})
                else:
                    self.send_json_response(500, {"success": False, "error": result.stderr or result.stdout})
            except Exception as e:
                self.send_json_response(500, {"success": False, "error": f"Failed to publish to Webflow: {str(e)}"})
            return

        self.send_response(404)
        self.end_headers()

    def send_json_response(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Aether Knowledge Factory Dashboard Local Server.")
    default_port = int(os.environ.get("PORT", 8000))
    parser.add_argument("--port", type=int, default=default_port, help="Port to bind the server to.")
    args = parser.parse_args()

    server_address = ("", args.port)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print(f"🚀 Aether Factory Dashboard running at: http://localhost:{args.port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server.")
        sys.exit(0)

if __name__ == "__main__":
    main()
