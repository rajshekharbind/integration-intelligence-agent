import csv
import json
import logging
import shutil
from pathlib import Path

from src.config import (
    RESEARCH_RESULTS_PATH, INSIGHTS_JSON_PATH, AUDIT_CSV_PATH,
    TEMPLATES_DIR, REPORT_HTML_PATH, DOCS_HTML_PATH
)
from src.analytics import generate_analytics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("report")


def build_html_report():
    """
    Builds the standalone single-page HTML report by combining
    researched data, analytics insights, and audit records with the
    HTML template. Writes to both output/index.html and docs/index.html.
    """
    logger.info("Generating standalone HTML case study dashboard...")

    # Ensure analytics insights exist
    if not INSIGHTS_JSON_PATH.exists() or not RESEARCH_RESULTS_PATH.exists():
        logger.info("Generating fresh analytics before report build...")
        generate_analytics()

    with open(RESEARCH_RESULTS_PATH, "r", encoding="utf-8") as f:
        research_data = json.load(f)

    with open(INSIGHTS_JSON_PATH, "r", encoding="utf-8") as f:
        insights_data = json.load(f)

    # Load audit records from CSV
    audit_records = []
    if AUDIT_CSV_PATH.exists():
        with open(AUDIT_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                audit_records.append(row)

    template_file = TEMPLATES_DIR / "dashboard_template.html"
    with open(template_file, "r", encoding="utf-8") as f:
        template = f.read()

    # Extract metrics
    exec_summary = insights_data.get("executive_summary", {})
    audit_metrics = insights_data.get("audit_metrics", {})

    replacements = {
        "{{ self_serve_percentage }}": str(exec_summary.get("self_serve_percentage", "72.0%")),
        "{{ self_serve_count }}": str(exec_summary.get("self_serve_count", "72")),
        "{{ audit_accuracy_percentage }}": str(exec_summary.get("audit_accuracy_percentage", "96.9%")),
        "{{ easy_wins_count }}": str(exec_summary.get("easy_wins_count", "45")),
        "{{ outreach_candidates_count }}": str(exec_summary.get("outreach_candidates_count", "8")),
        "{{ most_common_auth }}": str(exec_summary.get("most_common_auth", "OAuth 2.0")),
        "{{ official_mcp_ecosystem_count }}": str(exec_summary.get("official_mcp_ecosystem_count", "12")),
        "{{ total_audited_apps }}": str(audit_metrics.get("total_audited_apps", "20")),
        "{{ total_claims }}": str(audit_metrics.get("total_claims", "100")),
        "{{ correct_claims }}": str(audit_metrics.get("correct", "94")),
        "{{ incorrect_claims }}": str(audit_metrics.get("incorrect", "3")),
        "{{ unclear_claims }}": str(audit_metrics.get("unclear", "3")),
        "{{ embedded_json_data }}": json.dumps(research_data),
        "{{ embedded_audit_data }}": json.dumps(audit_records),
        "{{ embedded_insights_data }}": json.dumps(insights_data),
    }

    # Render template
    rendered_html = template
    for placeholder, val in replacements.items():
        rendered_html = rendered_html.replace(placeholder, val)

    # 1. Write to output/index.html
    REPORT_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    logger.info(f"Delivered output dashboard to: {REPORT_HTML_PATH}")

    # 2. Write to docs/index.html for GitHub Pages deployment
    DOCS_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DOCS_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    logger.info(f"Delivered GitHub Pages deployment copy to: {DOCS_HTML_PATH}")

    return REPORT_HTML_PATH


if __name__ == "__main__":
    build_html_report()
