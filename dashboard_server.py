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
            
            # Load active items (those having status == active)
            all_units = load_all_knowledge_units("knowledge")
            active_units = [u for u in all_units if u.get("status") == "active"]
            
            self.wfile.write(json.dumps(active_units).encode("utf-8"))
            return

        elif path == "/api/drafts":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            # Load pending drafts
            draft_units = []
            draft_dir = os.path.join("knowledge", "drafts")
            if os.path.exists(draft_dir):
                # Temporarily call load_all_knowledge_units on the drafts folder to parse them
                draft_units = load_all_knowledge_units(draft_dir)
            
            self.wfile.write(json.dumps(draft_units).encode("utf-8"))
            return

        # Fallback to standard handler
        return super().do_GET()

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

        elif path == "/api/generate":
            topic = query.get("topic", [""])[0]
            if not topic:
                self.send_json_response(400, {"success": False, "error": "Missing 'topic' query parameter."})
                return

            # Run orchestrator stage 1 using a subprocess
            print(f"⚡ Dashboard: Spawning orchestrator for topic: {topic}...")
            cmd = [sys.executable, "orchestrator.py", "--stage", "brief", "--topic", topic]
            try:
                # Inherit environment variables (including GEMINI_API_KEY if exported)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    self.send_json_response(200, {"success": True, "logs": result.stdout})
                else:
                    self.send_json_response(500, {"success": False, "error": result.stderr or result.stdout})
            except Exception as e:
                self.send_json_response(500, {"success": False, "error": f"Failed to run subprocess: {str(e)}"})
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
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to.")
    args = parser.parse_args()

    # Serve relative to project root
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
