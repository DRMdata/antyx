import os
import webbrowser
import pathlib
import requests
from flask import Flask, request, Response

from antyx.utils.visualizations import (
    visualizations,
    generate_viz_html,
)
from antyx.utils.lines import lines
from antyx.utils.summary import (
    describe_data,
    build_summary_dataframes,
    export_summary
)
from antyx.utils.correlations import correlation_analysis
from antyx.utils.profiles import variable_profiles
from .data_loader import DataLoader


class EDAReport:
    """
    Interactive EDA dashboard served via Flask + export to standalone HTML.
    """

    def __init__(self, file_path=None, df=None, theme="light", host="127.0.0.1", port=5000, use_polars=False):
        """
        EDAReport can load data from:
        - file_path (CSV, Excel, JSON, Parquet…)
        - pandas DataFrame
        - polars DataFrame (converted to pandas)
        """

        # --- INTELLIGENT INPUT DETECTION ---
        # If the first positional argument is a DataFrame, treat it as df
        if df is None and file_path is not None:
            try:
                import pandas as pd
                import polars as pl
                if isinstance(file_path, (pd.DataFrame, pl.DataFrame)):
                    df = file_path
                    file_path = None
            except ImportError:
                # If polars is not installed, only check pandas
                import pandas as pd
                if isinstance(file_path, pd.DataFrame):
                    df = file_path
                    file_path = None

        if file_path is None and df is None:
            raise ValueError("You must provide either file_path or df.")

        self.file_path = file_path
        self.df = None
        self.skipped_lines = 0
        self.encoding = None
        self.theme = theme
        self.host = host
        self.port = port
        self.use_polars = use_polars

        # Load data from DataFrame or file
        self._load_data(df)

        # Determine package root: antyx/
        self.PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]

        # Flask app serving antyx/ as static folder
        self.app = Flask(
            __name__,
            static_folder=str(self.PACKAGE_ROOT),
            static_url_path="/antyx"
        )

        # Register routes
        self._register_routes()


    # ---------------------------------------------------------
    # Load data
    # ---------------------------------------------------------
    def _load_data(self, df=None):
        """
        Loads data from:
        - Provided DataFrame (pandas or polars)
        - File path using DataLoader
        """

        # CASE 1 → DataFrame provided directly
        if df is not None:
            # Convert Polars → pandas
            try:
                import polars as pl
                if isinstance(df, pl.DataFrame):
                    df = df.to_pandas()
            except ImportError:
                pass

            # Validate pandas DataFrame
            import pandas as pd
            if not isinstance(df, pd.DataFrame):
                raise TypeError("df must be a pandas or polars DataFrame.")

            self.df = df.copy()
            self.encoding = "in-memory"
            self.skipped_lines = 0
            return

        # CASE 2 → Load from file
        loader = DataLoader(self.file_path, use_polars=self.use_polars)
        self.df = loader.load_data()

        if self.df is None:
            raise ValueError("Failed to load the file.")

        self.encoding = getattr(loader, "encoding", "utf-8")
        self.skipped_lines = loader.skipped_lines


    # ---------------------------------------------------------
    # Helpers for standalone HTML
    # ---------------------------------------------------------
    def _embed_css(self, relative_path):
        css_path = self.PACKAGE_ROOT / relative_path
        with open(css_path, "r", encoding="utf-8") as f:
            return f"<style>\n{f.read()}\n</style>"

    def _embed_all_css(self):
        css_files = [
            "styles/base.css",
            "styles/layout.css",
            "styles/tables.css",
            "styles/images.css",
            "styles/correlations.css",
            "styles/lines.css",
            "styles/summary.css",
            "styles/profiles.css",
            "styles/visualizations.css",
            f"styles/theme-{self.theme}.css",
        ]
        return "\n".join(self._embed_css(path) for path in css_files)

    def _embed_plotly(self):
        url = "https://cdn.plot.ly/plotly-latest.min.js"
        js = requests.get(url).text
        return f"<script>\n{js}\n</script>"

    # ---------------------------------------------------------
    # Generate standalone HTML
    # ---------------------------------------------------------
    def _generate_standalone_html(self):
        css = self._embed_all_css()
        plotly_js = self._embed_plotly()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Antyx</title>

            {css}
            {plotly_js}

            <script>
            function setThemeIcon(isDark) {{
              const iconSpan = document.getElementById("theme-icon");
              if (!iconSpan) return;

              if (isDark) {{
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
                iconSpan.innerHTML = `<svg class="icon-moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                    <path d="M15 2a8 8 0 1 0 7 11A6 6 0 1 1 15 2Z"
                    fill="currentColor"/>
                </svg>`;
              }}
            }}

            function toggleTheme() {{
              const body = document.body;
              const isDark = body.classList.toggle("dark");
              setThemeIcon(isDark);
            }}

            document.addEventListener("DOMContentLoaded", () => {{
              // Tema inicial: usa self.theme para fijar la clase
              if ("{self.theme}" === "dark") {{
                document.body.classList.add("dark");
              }}
              const isDark = document.body.classList.contains("dark");
              setThemeIcon(isDark);
            }});
            </script>

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

        <body class="{'dark' if self.theme == 'dark' else ''}">
            <div class="header">
                <div class="top-bar">
                    <div class="title-block">
                        <h1>Antyx</h1>
                        <span class="subtitle">Exploratory Data Analysis</span>
                    </div>

                    <div class="utilities-menu">
                        <div class="utilities-trigger">Utilities ▾</div>
                        <div class="utilities-dropdown">
                            <div class="utility-item" onclick="downloadReport()">Download report</div>
                        </div>
                    </div>

                    <nav class="main-menu">
                        <ul>
                            <li class="menu-item active" data-target="lines">
                                <span>Sample</span>
                            </li>
                            <li class="menu-item" data-target="desc">
                                <span>Summary</span>
                            </li>
                            <li class="menu-item" data-target="corr">
                                <span>Correlations</span>
                            </li>
                            <li class="menu-item" data-target="viz">
                                <span>Visualizations</span>
                            </li>
                            <li class="menu-item" data-target="prof">
                                <span>Profiles</span>
                            </li>

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
                    {lines(
                        self.df,
                        file_name=os.path.basename(self.file_path) if self.file_path else "",
                        total_records=self.df.shape[0] + self.skipped_lines,
                        omitted_records=self.skipped_lines,
                        theme=self.theme,
                        file_path=self.file_path
                    )}
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
            
            <div class="summary-export">
                <button class="export-icon" onclick="downloadSummaryExcel()">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <path d="M5 3h14v18H5z" stroke="currentColor" stroke-width="2"/>
                        <path d="M9 8l6 8M15 8l-6 8" stroke="currentColor" stroke-width="2"/>
                    </svg>
                </button>
            </div>

            <script>
            document.addEventListener("DOMContentLoaded", () => {{
                const trigger = document.querySelector(".utilities-trigger");
                const dropdown = document.querySelector(".utilities-dropdown");

                trigger.addEventListener("click", () => {{
                    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
                }});

                document.addEventListener("click", (e) => {{
                    if (!trigger.contains(e.target) && !dropdown.contains(e.target)) {{
                        dropdown.style.display = "none";
                    }}
                }});
            }});

            // Versión autónoma: descarga el propio HTML
            function downloadReport() {{
                const blob = new Blob([document.documentElement.outerHTML], {{ type: "text/html" }});
                const url = URL.createObjectURL(blob);

                const a = document.createElement("a");
                a.href = url;
                a.download = "antyx_report.html";
                a.click();

                URL.revokeObjectURL(url);
            }}
            </script>
            
            <script>
                function downloadSummaryExcel() {{
                    const content = document.querySelector("#desc").innerText;
                
                    const blob = new Blob([content], {{ type: "text/plain" }});
                    const url = URL.createObjectURL(blob);
                
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = "summary.txt";
                    a.click();
                
                    URL.revokeObjectURL(url);
                }}
                </script>
        </body>
        </html>
        """
        return html

    # ---------------------------------------------------------
    # Public method to save standalone HTML
    # ---------------------------------------------------------
    def save_html(self, output_path="antyx_report.html"):
        html = self._generate_standalone_html()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Standalone HTML saved to: {output_path}")

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
                    iconSpan.innerHTML = `<svg class="icon-moon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
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

                        <div class="utilities-menu">
                            <div class="utilities-trigger">Utilities ▾</div>
                            <div class="utilities-dropdown">
                                <div class="utility-item" onclick="downloadReport()">Download html</div>
                            </div>
                        </div>

                        <nav class="main-menu">
                            <ul>
                                <li class="menu-item active" data-target="lines">
                                    <span>Sample</span>
                                </li>
                                <li class="menu-item" data-target="desc">
                                    <span>Summary</span>
                                </li>
                                <li class="menu-item" data-target="corr">
                                    <span>Correlations</span>
                                </li>
                                <li class="menu-item" data-target="viz">
                                    <span>Visualizations</span>
                                </li>
                                <li class="menu-item" data-target="prof">
                                    <span>Profiles</span>
                                </li>

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
                        {lines(
                            self.df,
                            file_name=os.path.basename(self.file_path) if self.file_path else "",
                            total_records=self.df.shape[0] + self.skipped_lines,
                            omitted_records=self.skipped_lines,
                            theme=self.theme,
                            file_path=self.file_path
                        )}
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

                <script>
                document.addEventListener("DOMContentLoaded", () => {{
                    const trigger = document.querySelector(".utilities-trigger");
                    const dropdown = document.querySelector(".utilities-dropdown");

                    trigger.addEventListener("click", () => {{
                        dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
                    }});

                    document.addEventListener("click", (e) => {{
                        if (!trigger.contains(e.target) && !dropdown.contains(e.target)) {{
                            dropdown.style.display = "none";
                        }}
                    }});
                }});

                // Download via Flask
                function downloadReport() {{
                    window.location.href = "/export";
                }}
                </script>
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

        @self.app.route("/export")
        def export():
            html = self._generate_standalone_html()
            return Response(
                html,
                mimetype="text/html",
                headers={"Content-Disposition": "attachment; filename=antyx_report.html"}
            )

        @self.app.route("/export/summary_excel")
        def export_summary_excel():
            numeric_df, binary_df, categorical_df, datetime_df = build_summary_dataframes(self.df)

            import io
            import pandas as pd

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                if not numeric_df.empty:
                    numeric_df.to_excel(writer, sheet_name="Numeric", index=False)
                if not binary_df.empty:
                    binary_df.to_excel(writer, sheet_name="Binary", index=False)
                if not categorical_df.empty:
                    categorical_df.to_excel(writer, sheet_name="Categorical", index=False)
                if not datetime_df.empty:
                    datetime_df.to_excel(writer, sheet_name="Datetime", index=False)

            buffer.seek(0)

            return Response(
                buffer.read(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=summary.xlsx"}
            )

    # ---------------------------------------------------------
    # Run server
    # ---------------------------------------------------------
    def run(self, open_browser=True):
        url = f"http://{self.host}:{self.port}/"
        if open_browser:
            webbrowser.open(url)
        self.app.run(host=self.host, port=self.port, debug=False)