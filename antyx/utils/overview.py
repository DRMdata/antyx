import pandas as pd


def overview(
    df,
    file_name="",
    total_records=None,
    omitted_records=0,
    theme="light",
    file_path=None,
    summary_stats=None
):
    """
    Generates the HTML block for the Overview tab.
    Fully self-contained: no external file access.
    """

    # -----------------------------
    # 1. Metadata
    # -----------------------------
    effective_file_name = file_name if file_name else "In-memory DataFrame"
    rows = df.shape[0]
    cols = df.shape[1]

    # -----------------------------
    # 2. KPIs
    # -----------------------------
    missing_pct = summary_stats["missing_pct"]
    dup_pct = summary_stats["dup_pct"]
    high_card = summary_stats["high_cardinality"]
    memory_str = summary_stats["memory_str"]
    leakage = summary_stats["leakage_risk"]
    fe_complexity = summary_stats["fe_complexity"]

    leakage_class = "green" if not leakage else "yellow"

    quality_class = (
        "good" if missing_pct < 5 and dup_pct < 1 else
        "medium" if missing_pct < 15 else
        "bad"
    )

    # -----------------------------
    # 3. First/Last rows
    # -----------------------------
    first_html = df.head(5).to_html(classes="table-custom ov-table", index=False)
    last_html = df.tail(5).to_html(classes="table-custom ov-table", index=False)

    # -----------------------------
    # 4. HTML final
    # -----------------------------
    return f"""
        <!-- HEADER -->
        <section class="ov-header">
            <div class="ov-file-info">
                <h2 class="ov-file-name">{effective_file_name}</h2>
                <div class="ov-meta">
                    <span class="ov-meta-item">Size: {memory_str}</span>
                    <span class="ov-meta-item">Rows: {rows}</span>
                    <span class="ov-meta-item">Columns: {cols}</span>
                </div>
            </div>
        </section>

        <!-- KPI GRID -->
        <section class="ov-kpi-grid">

            <div class="ov-kpi-card">
                <div class="ov-kpi-title">
                    Missing ratio
                    <span class="ov-tip">
                        ⓘ
                        <span class="ov-tip-text">
                            Percentage of missing cells over the total number of cells in the dataset.
                        </span>
                    </span>
                </div>
                <div class="ov-kpi-value">{missing_pct:.2f}%</div>
            </div>

            <div class="ov-kpi-card">
                <div class="ov-kpi-title">
                    Duplicates
                    <span class="ov-tip">
                        ⓘ
                        <span class="ov-tip-text">
                            Percentage of duplicated rows in the dataset.
                        </span>
                    </span>
                </div>
                <div class="ov-kpi-value">{dup_pct:.2f}%</div>
            </div>

            <div class="ov-kpi-card">
                <div class="ov-kpi-title">
                    High cardinality
                    <span class="ov-tip">
                        ⓘ
                        <span class="ov-tip-text">
                            Number of categorical variables with more than 50 unique values.
                        </span>
                    </span>
                </div>
                <div class="ov-kpi-value">{high_card}</div>
            </div>

            <div class="ov-kpi-card">
                <div class="ov-kpi-title">
                    Memory footprint
                    <span class="ov-tip">
                        ⓘ
                        <span class="ov-tip-text">
                            Estimated memory usage of the dataset in RAM.
                        </span>
                    </span>
                </div>
                <div class="ov-kpi-value">{memory_str}</div>
            </div>

            <div class="ov-kpi-card">
                <div class="ov-kpi-title">
                    Leakage risk
                    <span class="ov-tip">
                        ⓘ
                        <span class="ov-tip-text">
                            Heuristic check for columns that may contain target-like information.
                        </span>
                    </span>
                </div>
                <div class="ov-kpi-semaforo {leakage_class}"></div>
            </div>

            <div class="ov-kpi-card">
                <div class="ov-kpi-title">
                    Feature complexity
                    <span class="ov-tip">
                        ⓘ
                        <span class="ov-tip-text">
                            Estimated complexity of feature engineering.
                        </span>
                    </span>
                </div>
                <div class="ov-kpi-value">{fe_complexity}</div>
            </div>

        </section>

        <!-- DATA PREVIEW -->
        <section class="ov-data-preview">
            <h3>Data preview</h3>

            <div class="ov-table-block">
                <h4>First rows</h4>
                {first_html}
            </div>

            <div class="ov-table-block">
                <h4>Last rows</h4>
                {last_html}
            </div>
        </section>

        <!-- QUALITY -->
        <section class="ov-quality">
            <h3>Data quality</h3>
            <div class="ov-quality-indicator {quality_class}"></div>
            <p class="ov-quality-note">
                Quick quality assessment based on missing values, duplicates and cardinality.
            </p>
        </section>
    """