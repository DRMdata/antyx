import os
import webbrowser
import pathlib
from flask import Flask, request, Response

from antyx.utils.visualizations import (
    visualizations,
    generate_viz_html,
)

from antyx.utils.summary import (
    describe_data,
    build_summary_dataframes,
)

from antyx.utils.correlations import correlation_analysis
from antyx.utils.profiles import variable_profiles
from antyx.utils.overview import overview

from antyx.assets import embed_multiple_css
from .data_loader import DataLoader


class EDAReport:
    """
    Interactive EDA dashboard served via Flask + export to standalone HTML.
    """

    def __init__(self, file_path=None, df=None, theme="light",
                 host="127.0.0.1", port=5000, use_polars=False):

        # Intelligent input detection
        if df is None and file_path is not None:
            try:
                import pandas as pd
                import polars as pl
                if isinstance(file_path, (pd.DataFrame, pl.DataFrame)):
                    df = file_path
                    file_path = None
            except ImportError:
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

        self._load_data(df)

        import antyx
        self.PACKAGE_ROOT = pathlib.Path(antyx.__file__).resolve().parent

        self.app = Flask(
            __name__,
            static_folder=str(self.PACKAGE_ROOT),
            static_url_path="/antyx"
        )

        self._register_routes()

    # ---------------------------------------------------------
    # Load data
    # ---------------------------------------------------------
    def _load_data(self, df=None):

        if df is not None:
            try:
                import polars as pl
                if isinstance(df, pl.DataFrame):
                    df = df.to_pandas()
            except ImportError:
                pass

            import pandas as pd
            if not isinstance(df, pd.DataFrame):
                raise TypeError("df must be a pandas or polars DataFrame.")

            self.df = df.copy()
            self.encoding = "in-memory"
            self.skipped_lines = 0
            return

        loader = DataLoader(self.file_path, use_polars=self.use_polars)
        self.df = loader.load_data()

        if self.df is None:
            raise ValueError("Failed to load the file.")

        self.encoding = getattr(loader, "encoding", "utf-8")
        self.skipped_lines = loader.skipped_lines

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _embed_all_css(self):
        css_files = [
            "base.css",
            "layout.css",
            "tables.css",
            "images.css",
            "correlations.css",
            "lines.css",
            "summary.css",
            "profiles.css",
            "visualizations.css",
            "overview.css",
            f"theme-{self.theme}.css",
        ]
        return embed_multiple_css(css_files)

    def _embed_plotly(self):
        # Plotly local, servido por Flask desde antyx/static/plotly.min.js
        return '<script src="/antyx/static/plotly.min.js"></script>'

    def _compute_summary_stats(self):
        df = self.df

        total_cells = df.shape[0] * df.shape[1]
        total_missing = df.isna().sum().sum()
        missing_pct = (total_missing / total_cells * 100) if total_cells else 0

        dup_count = df.duplicated().sum()
        dup_pct = (dup_count / df.shape[0] * 100) if df.shape[0] else 0

        high_card = sum(df[col].nunique(dropna=True) > 50 for col in df.columns)

        size_bytes = df.memory_usage(deep=True).sum()

        def format_size(n):
            for unit in ["B", "KB", "MB", "GB"]:
                if n < 1024:
                    return f"{n:.2f} {unit}"
                n /= 1024
            return f"{n:.2f} TB"

        memory_str = format_size(size_bytes)

        leakage = any(col.lower() in ["target", "label", "outcome", "y", "class"] for col in df.columns)

        from antyx.utils.types import detect_var_type
        fe_complexity = sum(
            detect_var_type(df[col]) in ["categorical", "datetime", "other"] or
            df[col].nunique(dropna=True) > 50
            for col in df.columns
        )

        return {
            "missing_pct": missing_pct,
            "dup_pct": dup_pct,
            "high_cardinality": high_card,
            "memory_str": memory_str,
            "leakage_risk": leakage,
            "fe_complexity": fe_complexity,
        }

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
                            <li class="menu-item active" data-target="overview"><span>Overview</span></li>
                            <li class="menu-item" data-target="desc"><span>Summary</span></li>
                            <li class="menu-item" data-target="corr"><span>Correlations</span></li>
                            <li class="menu-item" data-target="viz"><span>Visualizations</span></li>
                            <li class="menu-item" data-target="prof"><span>Profiles</span></li>

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

                <div id="overview" class="tab-content active">
                    {overview(
                        self.df,
                        file_name=os.path.basename(self.file_path) if self.file_path else "",
                        total_records=self.df.shape[0] + self.skipped_lines,
                        omitted_records=self.skipped_lines,
                        theme=self.theme,
                        file_path=self.file_path,
                        summary_stats=self._compute_summary_stats()
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

            <!-- Navigation -->
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
                            if (sec.id === target) {{
                                sec.classList.add("active");

                                // Redraw Plotly graphs when tab becomes visible
                                setTimeout(() => {{
                                    if (window.Plotly) {{
                                        sec.querySelectorAll('.plotly-graph-div').forEach(g => {{
                                            try {{
                                                Plotly.Plots.resize(g);
                                            }} catch (e) {{}}
                                        }});
                                    }}
                                }}, 50);

                            }} else {{
                                sec.classList.remove("active");
                            }}
                        }});

                        window.scrollTo({{ top: 0, behavior: "instant" }});
                    }});
                }});
            }});
            </script>

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
              const body = document.body;
              const isDark = body.classList.toggle("dark");
              setThemeIcon(isDark);
            }}

            document.addEventListener("DOMContentLoaded", () => {{
              if ("{self.theme}" === "dark") {{
                document.body.classList.add("dark");
              }}
              const isDark = document.body.classList.contains("dark");
              setThemeIcon(isDark);
            }});
            </script>

            <!-- Utilities -->
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

        </body>
        </html>
        """

        return html

    # ---------------------------------------------------------
    # Public method
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
            return self._generate_standalone_html()

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

        @self.app.route("/export/summary_excel")
        def export_summary_excel():
            numeric_df, binary_df, categorical_df, datetime_df = build_summary_dataframes(self.df)[1:5]

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