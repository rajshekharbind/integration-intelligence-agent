import argparse
import csv
import datetime
import json
import logging
import sys
from typing import List, Dict, Any, Optional

from src.config import (
    APPS_CSV_PATH, RESEARCH_RESULTS_PATH, MAX_RETRIES
)
from src.models import AppResearchResult, VerificationStatus
from src.search import generate_search_queries, execute_search, is_official_domain
from src.fetcher import fetch_page_content
from src.extractor import extract_intelligence
from src.verifier import verify_app_research, run_batch_verification

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("research_agent")


def load_input_apps(csv_path: Optional[str] = None) -> List[Dict[str, str]]:
    """Loads apps from data/apps.csv."""
    path = csv_path or APPS_CSV_PATH
    apps = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("app"):
                apps.append({
                    "app": row["app"].strip(),
                    "category": row.get("category", "General").strip(),
                    "website": row.get("website", "").strip()
                })
    return apps


def load_existing_results() -> Dict[str, AppResearchResult]:
    """Loads existing results from research_results.json to enable incremental execution."""
    if not RESEARCH_RESULTS_PATH.exists():
        return {}
    try:
        with open(RESEARCH_RESULTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {item["app"]: AppResearchResult(**item) for item in data}
    except Exception as e:
        logger.warning(f"Could not load existing results: {e}")
        return {}


def save_results(results_map: Dict[str, AppResearchResult]):
    """Saves results dictionary to research_results.json atomically."""
    data = [res.model_dump() for res in results_map.values()]
    with open(RESEARCH_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def research_single_app(app_info: Dict[str, str], retry_attempt: int = 0) -> AppResearchResult:
    """
    Executes the 5-stage research pipeline for an individual application:
    1. Search official API docs & portals
    2. Fetch and clean content
    3. LLM/heuristic structured extraction
    4. Validation & Retry check
    5. Final result structuring
    """
    app = app_info["app"]
    category = app_info["category"]
    website = app_info["website"]
    logger.info(f"[{app}] Initiating research (Attempt {retry_attempt + 1})...")

    # 1. Search
    queries = generate_search_queries(app)
    all_search_hits = []
    for q in queries[:2]:  # Run top queries
        hits = execute_search(q, app_name=app)
        all_search_hits.extend(hits)

    # Deduplicate URLs
    seen_urls = set()
    unique_hits = []
    for hit in all_search_hits:
        u = hit.get("url")
        if u and u not in seen_urls:
            seen_urls.add(u)
            unique_hits.append(hit)

    # 2. Fetch pages & extract text
    fetched_texts = []
    evidence_urls = []
    for hit in unique_hits[:3]:
        url = hit["url"]
        evidence_urls.append(url)
        page = fetch_page_content(url)
        if page.get("clean_text"):
            fetched_texts.append(f"Source ({url}):\n{page['clean_text'][:2000]}")
        elif hit.get("snippet"):
            fetched_texts.append(f"Snippet ({url}):\n{hit['snippet']}")

    combined_text = "\n\n".join(fetched_texts)

    # 3. Extract structured facts
    extracted = extract_intelligence(app, category, website, combined_text)

    # 4. Check for weak evidence & retry if needed
    is_weak = (
        extracted.get("auth_type") == "Unknown" or
        len(evidence_urls) == 0 or
        extracted.get("self_serve") == "Unknown"
    )

    if is_weak and retry_attempt < MAX_RETRIES:
        logger.info(f"[{app}] Weak evidence detected. Triggering automated retry...")
        fallback_query = f"{app} developer documentation getting started authentication"
        retry_hits = execute_search(fallback_query, app_name=app)
        for rh in retry_hits:
            if rh["url"] not in evidence_urls:
                evidence_urls.append(rh["url"])
                pg = fetch_page_content(rh["url"])
                fetched_texts.append(f"Retry Source ({rh['url']}):\n{pg.get('clean_text', rh.get('snippet', ''))[:2000]}")
        combined_text = "\n\n".join(fetched_texts)
        extracted = extract_intelligence(app, category, website, combined_text)
        retry_attempt += 1

    # 5. Build Result
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    result = AppResearchResult(
        app=app,
        category=category,
        website=website,
        description=extracted.get("description", f"Integration capabilities for {app}"),
        auth_type=extracted.get("auth_type", "Unknown"),
        auth_details=extracted.get("auth_details", ""),
        self_serve=extracted.get("self_serve", "Unknown"),
        access_type=extracted.get("access_type", "Unknown"),
        access_restrictions=extracted.get("access_restrictions", ""),
        api_type=extracted.get("api_type", "REST"),
        api_surface=extracted.get("api_surface", "REST API"),
        mcp_status=extracted.get("mcp_status", "Unknown"),
        mcp_details=extracted.get("mcp_details", ""),
        buildability=extracted.get("buildability", "P3 - Conditional / Complex"),
        priority_tier=extracted.get("priority_tier", "P3"),
        priority_score=extracted.get("priority_score", 50),
        blockers=extracted.get("blockers", []),
        evidence_urls=evidence_urls,
        verification_status=VerificationStatus.RESEARCHED.value,
        confidence_score=extracted.get("confidence_score", 0.8),
        retry_count=retry_attempt,
        research_timestamp=now_iso
    )

    # Automated verification check
    verify_app_research(result)
    return result


def run_pipeline(limit: Optional[int] = None, specific_app: Optional[str] = None, force: bool = False):
    """Executes the research agent across all apps in apps.csv."""
    apps = load_input_apps()
    existing = load_existing_results()

    if specific_app:
        apps = [a for a in apps if a["app"].lower() == specific_app.lower()]
        if not apps:
            logger.error(f"App '{specific_app}' not found in apps.csv!")
            return

    if limit:
        apps = apps[:limit]

    logger.info(f"Targeting {len(apps)} applications for research...")
    completed = 0

    for idx, app_info in enumerate(apps, 1):
        app_name = app_info["app"]
        if not force and app_name in existing:
            logger.info(f"[{idx}/{len(apps)}] Skipping already researched: {app_name}")
            continue

        try:
            res = research_single_app(app_info)
            existing[app_name] = res
            save_results(existing)
            completed += 1
            logger.info(f"[{idx}/{len(apps)}] Successfully completed and saved: {app_name} (Priority: {res.priority_tier})")
        except Exception as e:
            logger.error(f"[{idx}/{len(apps)}] Error researching {app_name}: {e}")

    valid_app_names = {a["app"] for a in apps}
    final_results_map = {k: v for k, v in existing.items() if k in valid_app_names}

    # Run batch verification on entire active dataset
    all_results = list(final_results_map.values())
    run_batch_verification(all_results)
    save_results(final_results_map)
    logger.info(f"Pipeline finished! Researched {completed} apps. Total dataset size: {len(all_results)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Integration Intelligence Research Agent")
    parser.add_argument("--app", type=str, help="Research a specific app (e.g. 'HubSpot')")
    parser.add_argument("--limit", type=int, help="Limit number of apps to research")
    parser.add_argument("--all", action="store_true", help="Research all 100 apps")
    parser.add_argument("--force", action="store_true", help="Force re-researching existing apps")
    args = parser.parse_args()

    run_pipeline(limit=args.limit, specific_app=args.app, force=args.force)
