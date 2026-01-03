import webbrowser
import os

from .data_loader import DataLoader
from antyx.utils.lines import lines
from antyx.utils.summary import describe_data
from antyx.utils.outliers import detect_outliers
from antyx.utils.correlations import correlation_analysis
from antyx.utils.visualizations import basic_visuals


class EDAReport:
    """Class for generating an Exploratory Data Analysis (EDA) report.

    This class loads data from a file (using DataLoader) and generates
    an HTML report with summaries, outliers, correlations, and visualizations.

    Attributes:
        file_path (str): Path to the data file.
        df (pd.DataFrame): DataFrame with the loaded data.
        skipped_lines (int): Number of lines skipped during loading.
        encoding (str): Encoding used to load the file.

    Example:
        >>> report = EDAReport("data/dataset.csv")
        >>> report.generate_html("eda_report.html")
    """

    def __init__(self, file_path):
        """Initializes the report generator with the file path.

        Args:
            file_path (str): Path to the data file.
        """
        self.file_path = file_path
        self.df = None
        self.skipped_lines = 0
        self.encoding = None
        self._load_data()

    def _load_data(self):
        """Loads data using DataLoader."""
        loader = DataLoader(self.file_path)
        self.df = loader.load_data()
        if self.df is not None:
            self.encoding = getattr(loader, 'encoding', 'utf-8')
            self.skipped_lines = loader.skipped_lines
        else:
            raise ValueError("Failed to load the file.")

    def generate_html(self, output_path='eda_report.html', open_browser=True, theme="light"):
        """
        Generates an HTML report with exploratory data analysis.

        Args:
            output_path (str): Path to save the HTML report.
            open_browser (bool): If True, opens the report in the browser.

        Example:
            report = EDAReport("data/dataset.csv")
            report.generate_html("report.html")
        """
        if self.df is None:
            raise ValueError("No data loaded to generate the report.")

        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            
            <title>Antyx</title>
            
            <button onclick="toggleTheme()" 
                    style="position:fixed; top:20px; right:20px; padding:10px 20px;">
                Toggle Theme
            </button>
            
            <script>
            function toggleTheme() {{
                document.body.classList.toggle("dark");
            
                // Forzar repaint solo en la pestaña activa
                const activeTab = document.querySelector(".tab-content.active");
                if (activeTab) {{
                    activeTab.classList.add("force-repaint");
                    void activeTab.offsetHeight; // reflow
                    activeTab.classList.remove("force-repaint");
                }}
            
                // Actualizar Plotly (si lo tienes)
                const isDark = document.body.classList.contains("dark");
                const plots = document.getElementsByClassName("plotly-graph-div");
                for (let p of plots) {{
                    Plotly.relayout(p, {{
                        paper_bgcolor: isDark ? "#1e1e1e" : "white",
                        plot_bgcolor: isDark ? "#1e1e1e" : "white",
                        font: {{color: isDark ? "#e0e0e0" : "#333"}},
                        "xaxis.tickfont.color": isDark ? "#e0e0e0" : "#333",
                        "yaxis.tickfont.color": isDark ? "#e0e0e0" : "#333",
                        "xaxis.titlefont.color": isDark ? "#e0e0e0" : "#333",
                        "yaxis.titlefont.color": isDark ? "#e0e0e0" : "#333"
                    }});
                }}
            }}
            </script>
            
            <style>
                .force-repaint {{
                    transform: scale(1);
                }}
                
                :root {{
                    --font-family: Arial, sans-serif;
                
                    /* Light theme */
                    --bg-color: #f8f8f8;
                    --text-color: #333;
                    --accent-color: #1E90FE;
                    --card-bg: #ffffff;
                
                    --table-header-bg: #eaeaea;
                    --table-border-color: #ccc;
                    --table-hover-bg: #e6f7ff;
                
                    --tab-bg: #ffffff;
                    --tab-text: #1E90FE;
                    --tab-active-bg: #1E90FE;
                    --tab-active-text: #ffffff;
                }}
                
                body.dark {{
                    --font-family: Arial, sans-serif;
                
                    /* Dark theme */
                    --bg-color: #1e1e1e;
                    --text-color: #e0e0e0;
                    --accent-color: #4aa3ff;
                    --card-bg: #2a2a2a;
                
                    --table-header-bg: #3a3a3a;
                    --table-border-color: #555;
                    --table-hover-bg: #333;
                
                    --tab-bg: #2a2a2a;
                    --tab-text: #4aa3ff;
                    --tab-active-bg: #4aa3ff;
                    --tab-active-text: #1e1e1e;
                }}             

                body {{
                    font-family: var(--font-family);
                    margin: 0;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    padding: 20px;
                }}

                .header {{
                    display: flex;
                    align-items: center;
                    margin-bottom: 20px;
                }}

                h1 {{
                    font-size: 45px;
                    background-size: cover;
                    background-position: center;
                    color: #1E90FE;
                    padding: 20px;
                    margin: 0 0 10px 0;
                    text-align: left;
                }}

                .file-name {{
                    font-size: 18px;
                    color: #1E90FE;
                    margin: 0;
                    text-align: left;
                }}

                .container {{
                    display: flex;
                    flex-direction: column;
                    align-items: flex-start;
                }}

                .tabs {{
                    display: flex;
                    border-bottom: 2px solid #1E90FE;
                    margin-bottom: 20px;
                    width: 100%;
                }}

                .tab-link {{
                    padding: 15px 30px;
                    cursor: pointer;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    border: 1px solid var(--accent-color);
                    border-bottom: none;
                    font-weight: bold;
                    margin-right: 5px;
                    border-top-left-radius: 6px;
                    border-top-right-radius: 6px;
                    transition: background-color 0.3s, transform 0.2s;
                }}

                .tab-link:hover {{
                    background-color: var(--table-hover-bg);
                    transform: translateY(-2px);
                }}

                .tab-link.active {{
                    background-color: var(--tab-active-bg);
                    color: var(--tab-active-text);
                }}

                .tab-content {{
                    animation: fadeIn 0.4s ease-in-out;
                    width: 100%;
                    padding: 20px;
                    box-sizing: border-box;
                    display: none;
                }}

                .tab-content.active {{
                    display: block;
                }}

                @keyframes fadeIn {{
                    from {{opacity: 0; }}
                    to {{opacity: 1; }}
                }}
                
                .corr-container {{
                    width: 100%;
                    max-width: 100%;
                }}
                
                /* Container for tables with horizontal scrolling */
                .table-container {{
                    width: 100%;
                    overflow-x: auto;
                    margin: 20px 0;
                }}

                /* Styles for fixed-width tables */
                .table-custom {{
                    border-collapse: collapse;
                    table-layout: fixed;
                    width: auto;
                    margin: 0;
                    font-family: Arial, sans-serif;
                }}

                .table-custom th, .table-custom td {{
                    border - left: none;
                    border-right: none;
                    border-top: 1px solid var(--table-border-color);
                    border-bottom: 1px solid var(--table-border-color);
                    padding: 8px;
                    text-align: right;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}

                .table-custom th {{
                    background-color: var(--table-header-bg);
                    color: var(--text-color);
                    text-align: center;
                }}

                .table-custom td:first-child {{
                    text-align: left;
                }}

                .table-custom td.empty {{
                    background-color: #f9f9f9;
                    color: #ccc;
                }}

                .table-custom th:nth-child(1),
                .table-custom td:nth-child(1) {{
                    width: 200px !important;
                    min-width: 200px !important;
                    max-width: 200px !important;
                    text-align: left !important;
                }}

                .table-custom th:nth-child(2),
                .table-custom td:nth-child(2) {{
                    width: 75px !important;
                    min-width: 75px !important;
                    max-width: 75px !important;
                    text-align: left !important;
                }}

                .table-custom td {{
                    font-family: 'Courier New', monospace;
                }}

                /* Tooltip to display the full content when hovering over it */
                .table-custom td,
                .table-custom th {{
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}

                /* Optional style to improve the appearance of the tooltip */
                .table-custom td:hover,
                .table-custom th:hover {{
                    cursor: default;
                }}

                .table-custom td.group1 {{
                    background-color: #e6f2ff;
                    width: 100px !important;
                    min-width: 100px !important;
                    max-width: 100px !important;
                }}

                .table-custom td.group2 {{
                    background-color: #d0e7ff;
                    width: 100px !important;
                    min-width: 100px !important;
                    max-width: 100px !important;
                }}

                .table-custom td.group3 {{
                    background-color: #c2dbf7;
                    width: 100px !important;
                    min-width: 100px !important;
                    max-width: 100px !important;
                }}

                .table-custom td.group4 {{
                    background-color: #b3d1f0;
                    width: 100px !important;
                    min-width: 100px !important;
                    max-width: 100px !important;
                }}

                img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                }}
            </style>

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
                <h1>Antyx</h1>
            </div>
            <div class="container">
                <div class="file-info">
                    <p><strong>File:</strong> {os.path.basename(self.file_path)}</p>
                    <p><strong>Loaded lines:</strong> {len(self.df)}</p>
                    <p><strong>Omitted lines:</strong> {self.skipped_lines}</p>
                </div>
                <div class="tabs">
                    <div class="tab-link active" onclick="openTab(event, 'lines')">Lines</div>
                    <div class="tab-link" onclick="openTab(event, 'desc')">Summary</div>
                    <div class="tab-link" onclick="openTab(event, 'outliers')">Outliers</div>
                    <div class="tab-link" onclick="openTab(event, 'corr')">Correlations</div>
                    <div class="tab-link" onclick="openTab(event, 'viz')">Visualizations</div>
                </div>
                <div id="lines" class="tab-content active">{lines(self.df)}</div>
                <div id="desc" class="tab-content">{describe_data(self.df)}</div>
                <div id="outliers" class="tab-content">{detect_outliers(self.df)}</div>
                <div id="corr" class="tab-content">{correlation_analysis(self.df)}</div>
                <div id="viz" class="tab-content">{basic_visuals(self.df)}</div>
            </div>
        </body>
        </html>
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Report generated: {output_path}")
        if open_browser:
            file_url = f'file://{os.path.abspath(output_path)}'
            webbrowser.open(file_url)
