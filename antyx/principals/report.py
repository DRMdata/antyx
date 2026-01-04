import os
import webbrowser
import pathlib
from flask import Flask, request

from antyx.utils.visualizations import (
    visualizations,
    generate_viz_html,
    generate_viz_figure,
    export_figure,
)
from antyx.utils.lines import lines
from antyx.utils.summary import describe_data
from antyx.utils.outliers import detect_outliers
from antyx.utils.correlations import correlation_analysis
from .data_loader import DataLoader


class EDAReport:
    """
    Interactive EDA dashboard served via Flask (architecture C).
    """

    def __init__(self, file_path, theme="light", host="127.0.0.1", port=5000):
        self.file_path = file_path
        self.df = None
        self.skipped_lines = 0
        self.encoding = None
        self.theme = theme
        self.host = host
        self.port = port

        # Load data
        self._load_data()

        # Determine package root: antyx/
        PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]

        # Flask app serving antyx/ as static folder
        self.app = Flask(
            __name__,
            static_folder=str(PACKAGE_ROOT),
            static_url_path="/antyx"
        )

        # Register routes
        self._register_routes()

    # ---------------------------------------------------------
    # Load data
    # ---------------------------------------------------------
    def _load_data(self):
        loader = DataLoader(self.file_path)
        self.df = loader.load_data()
        if self.df is not None:
            self.encoding = getattr(loader, "encoding", "utf-8")
            self.skipped_lines = loader.skipped_lines
        else:
            raise ValueError("Failed to load the file.")

    # ---------------------------------------------------------
    # Flask routes
    # ---------------------------------------------------------
    def _register_routes(self):

        @self.app.route("/")
        def index():
            file_name = os.path.basename(self.file_path)
            loaded_lines = len(self.df)
            omitted_lines = self.skipped_lines

            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Antyx</title>
                
                <!-- Plotly -->
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                
                <!-- CSS -->
                <link rel="stylesheet" href="/antyx/styles/base.css">
                <link rel="stylesheet" href="/antyx/styles/layout.css">
                <link rel="stylesheet" href="/antyx/styles/tabs.css">
                <link rel="stylesheet" href="/antyx/styles/tables.css">
                <link rel="stylesheet" href="/antyx/styles/images.css">
                <link rel="stylesheet" href="/antyx/styles/correlations.css">
                <link rel="stylesheet" href="/antyx/styles/lines.css">
                <link rel="stylesheet" href="/antyx/styles/summary.css">
                <link rel="stylesheet" href="/antyx/styles/visualizations.css">

                <link id="theme" rel="stylesheet" href="/antyx/styles/theme-{self.theme}.css">

                <!-- Theme toggle -->
                <script>
                function toggleTheme() {{
                    const link = document.getElementById("theme");
                    const current = link.getAttribute("href");

                    if (current.endsWith("theme-light.css")) {{
                        link.setAttribute("href", "/antyx/styles/theme-dark.css");
                    }} else {{
                        link.setAttribute("href", "/antyx/styles/theme-light.css");
                    }}
                }}
                </script>

                <!-- Tabs -->
                <script>
                function openTab(evt, tabId) {{
                    var i, tabcontent, tablinks;
                    tabcontent = document.getElementsByClassName("tab-content");
                    for (i = 0; i < tabcontent.length; i++) {{
                        tabcontent[i].classList.remove("active");
                    }}
                    tablinks = document.getElementsByClassName("tab-link");
                    for (i = 0; i < tablinks.length; i++) {{
                        tablinks[i].classList.remove("active");
                    }}
                    document.getElementById(tabId).classList.add("active");
                    evt.currentTarget.classList.add("active");
                }}
                </script>
            </head>

            <body>
                <div class="header">
                    <div class="top-bar">
                        <div class="title-block">
                            <h1>Antyx</h1>
                            <p></p>
                            <span class="subtitle">Exploratory Data Analysis</span>
                        </div>
                        <button id="theme-toggle" class="theme-toggle-btn" onclick="toggleTheme()">
                            <img src="/antyx/icons/toggle-icon.svg" class="theme-icon" alt="Toggle theme">
                        </button>
                    </div>
                </div>
                <div class="container">
                    <div class="file-info">
                        <p><strong>File:</strong> {file_name}</p>
                        <p><strong>Loaded lines:</strong> {loaded_lines}</p>
                        <p><strong>Omitted lines:</strong> {omitted_lines}</p>
                        <p></p>
                    </div>

                    <div class="tabs">
                        <div class="tab-link active" onclick="openTab(event, 'lines')">Lines</div>
                        <div class="tab-link" onclick="openTab(event, 'desc')">Summary</div>
                        <div class="tab-link" onclick="openTab(event, 'corr')">Correlations</div>
                        <div class="tab-link" onclick="openTab(event, 'viz')">Visualizations</div>
                    </div>

                    <div id="lines" class="tab-content active">
                        {lines(self.df)}
                    </div>

                    <div id="desc" class="tab-content">
                        {describe_data(self.df, output_dir=os.getcwd())}
                    </div>

                    <div id="corr" class="tab-content">
                        {correlation_analysis(self.df, theme=self.theme)}
                    </div>

                    <div id="viz" class="tab-content">
                        {visualizations(self.df, theme=self.theme)}
                    </div>
                </div>
            </body>
            </html>
            """
            return html

        @self.app.route("/viz", methods=["POST"])
        def viz():
            data = request.json or {}
            vars_ = data.get("vars", [])
            viz_type = data.get("type", None)

            return generate_viz_html(
                self.df,
                vars_,
                viz_type,
                self.theme,
            )

        @self.app.route("/viz-export", methods=["POST"])
        def viz_export():
            data = request.json or {}
            vars_ = data.get("vars", [])
            viz_type = data.get("type", None)

            fig = generate_viz_figure(
                self.df,
                vars_,
                viz_type,
                self.theme,
            )

            if fig is None:
                return "No figure to export."

            export_dir = os.getcwd()
            path = export_figure(fig, output_dir=export_dir)
            return path

    # ---------------------------------------------------------
    # Run server
    # ---------------------------------------------------------
    def run(self, open_browser=True):
        url = f"http://{self.host}:{self.port}/"
        if open_browser:
            webbrowser.open(url)
        self.app.run(host=self.host, port=self.port, debug=False)