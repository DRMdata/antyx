import os
import webbrowser
from flask import Flask, send_from_directory, render_template_string

def run_server(report_path, figs_dir, static_dir, port=8765):
    app = Flask(__name__)

    @app.route("/")
    def index():
        with open(report_path, "r", encoding="utf-8") as f:
            html = f.read()
        return render_template_string(html)

    @app.route("/figs/<path:path>")
    def serve_figs(path):
        return send_from_directory(figs_dir, path)

    @app.route("/static/<path:path>")
    def serve_static(path):
        return send_from_directory(static_dir, path)

    @app.route("/antyx/static/<path:path>")
    def serve_antyx_static(path):
        return send_from_directory(static_dir, path)

    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    url = f"http://localhost:{port}"
    webbrowser.open(url)

    print(f"Antyx server running at {url}")
    app.run(port=port, debug=False)