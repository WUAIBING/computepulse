import http.server
import socketserver
import json
import os
import mimetypes

PORT = 3001
DATA_FILE = os.path.abspath('gpu_prices.json')
TOKEN_FILE = os.path.abspath('token_prices.json')
GRID_FILE = os.path.abspath('grid_load.json')
DIST_DIR = os.path.abspath('dist')

class DataHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Handle API routes
        if self.path.startswith('/api/'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            if self.path == '/api/prices':
                file_path = DATA_FILE
            elif self.path == '/api/tokens':
                file_path = TOKEN_FILE
            elif self.path == '/api/grid':
                file_path = GRID_FILE
            else:
                self.wfile.write(json.dumps({'error': 'Not found'}).encode())
                return

            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            else:
                self.wfile.write(json.dumps([] if 'grid' not in self.path else {}).encode())
            return

        # Serve static files from DIST_DIR
        # Map / to index.html
        if self.path == '/':
            self.path = '/index.html'
        
        # Construct full path
        full_path = os.path.join(DIST_DIR, self.path.lstrip('/'))
        
        # If file exists, serve it
        if os.path.exists(full_path) and os.path.isfile(full_path):
            self.send_response(200)
            # Guess MIME type
            mime_type, _ = mimetypes.guess_type(full_path)
            if mime_type:
                self.send_header('Content-type', mime_type)
            self.end_headers()
            with open(full_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            # Fallback for SPA (if we were using routing, but we aren't really)
            # Or just 404
            self.send_error(404, "File not found")

print(f"Server running at http://localhost:{PORT}")
print(f"Serving static files from: {DIST_DIR}")

# Ensure dist exists (create empty if not for now, just to avoid crash)
if not os.path.exists(DIST_DIR):
    os.makedirs(DIST_DIR, exist_ok=True)
    print("Warning: 'dist' directory not found. Please run 'npm run build'.")

with socketserver.TCPServer(("", PORT), DataHandler) as httpd:
    httpd.serve_forever()
