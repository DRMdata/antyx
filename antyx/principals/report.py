import os
import webbrowser
import pathlib
from flask import Flask, request

from antyx.utils.visualizations import (
    visualizations,
    generate_viz_html,
)
from antyx.utils.lines import lines
from antyx.utils.summary import describe_data
from antyx.utils.correlations import correlation_analysis
from antyx.utils.profiles import variable_profiles
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
                <link rel="stylesheet" href="/antyx/styles/tables.css">
                <link rel="stylesheet" href="/antyx/styles/images.css">
                <link rel="stylesheet" href="/antyx/styles/correlations.css">
                <link rel="stylesheet" href="/antyx/styles/lines.css">
                <link rel="stylesheet" href="/antyx/styles/summary.css">
                <link rel="stylesheet" href="/antyx/styles/profiles.css">
                <link rel="stylesheet" href="/antyx/styles/visualizations.css">

                <link id="theme" rel="stylesheet" href="/antyx/styles/theme-{self.theme}.css">

                <!-- Theme toggle -->
                <script>
                function setThemeIcon(isDark) {{
                  const iconSpan = document.getElementById("theme-icon");
                  if (!iconSpan) return;
                
                  if (isDark) {{
                    // Mostrar sol (tema oscuro → cambiar a claro)
                    iconSpan.innerHTML = `
                      <svg class="icon-sun" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="4" fill="currentColor"/>
                        <g stroke="currentColor" stroke-width="2" stroke-linecap="round">
                          <line x1="12" y1="2" x2="12" y2="5"/>
                          <line x1="12" y1="19" x2="12" y2="22"/>
                          <line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/>
                          <line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/>
                          <line x1="2" y1="12" x2="5" y2="12"/>
                          <line x1="19" y1="12" x2="22" y2="12"/>
                          <line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/>
                          <line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/>
                        </g>
                      </svg>`;
                  }} else {{
                    // Mostrar luna (tema claro → cambiar a oscuro)
                    iconSpan.innerHTML = `<svg class="icon-moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <!-- Luna creciente -->
                        <path d="M15 2a8 8 0 1 0 7 11A6 6 0 1 1 15 2Z"
                        fill="currentColor"/>
                    </svg>`;
                  }}
                }}
                
                function toggleTheme() {{
                  const link = document.getElementById("theme");
                  const current = link.getAttribute("href");
                  const isLight = current.endsWith("theme-light.css");
                
                  link.setAttribute("href", isLight
                    ? "/antyx/styles/theme-dark.css"
                    : "/antyx/styles/theme-light.css");
                
                  setThemeIcon(isLight);
                }}
                
                document.addEventListener("DOMContentLoaded", () => {{
                  const current = document.getElementById("theme").getAttribute("href");
                  const isDark = current.endsWith("theme-dark.css");
                  setThemeIcon(isDark);
                }});
                </script>

                <!-- Section switching -->
                <script>
                document.addEventListener("DOMContentLoaded", () => {{
                    const items = document.querySelectorAll(".menu-item");
                    const sections = document.querySelectorAll(".tab-content");

                    items.forEach(item => {{
                        item.addEventListener("click", () => {{
                            const target = item.getAttribute("data-target");

                            items.forEach(i => i.classList.remove("active"));
                            item.classList.add("active");

                            sections.forEach(sec => {{
                                sec.classList.remove("active");
                                if (sec.id === target) sec.classList.add("active");
                            }});
                        }});
                    }});
                }});
                </script>
            </head>

            <body>
                <div class="header">
                    <div class="top-bar">
                        <div class="title-block">
                            <h1>Antyx</h1>
                            <span class="subtitle">Exploratory Data Analysis</span>
                        </div>

                        <nav class="main-menu">
                            <ul>
                                <li class="menu-item active" data-target="lines">Sample</li>
                                <li class="menu-item" data-target="desc">Summary</li>
                                <li class="menu-item" data-target="corr">Correlations</li>
                                <li class="menu-item" data-target="viz">Visualizations</li>
                                <li class="menu-item" data-target="prof">Profiles</li>

                                <li class="theme-toggle">
                                  <button id="theme-toggle" onclick="toggleTheme()">
                                    <span id="theme-icon"></span>
                                  </button>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>

                <div class="container">

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

                    <div id="prof" class="tab-content">
                        {variable_profiles(self.df, theme=self.theme)}
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

    # ---------------------------------------------------------
    # Run server
    # ---------------------------------------------------------
    def run(self, open_browser=True):
        url = f"http://{self.host}:{self.port}/"
        if open_browser:
            webbrowser.open(url)
        self.app.run(host=self.host, port=self.port, debug=False)