"""
Automated Diagnostic & Verification Script for Integration Intelligence Agent
Verifies live connectivity for Tavily Search API, Google Gemini API, and GitHub Pages deployment.
"""
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

def run_diagnostics():
    print("=" * 60)
    print("  INTEGRATION INTELLIGENCE AGENT - SYSTEM DIAGNOSTICS")
    print("=" * 60)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()

    # 1. Test Tavily API
    print("\n[1/4] Checking Tavily Search API...")
    if not tavily_key:
        print("  ❌ FAIL: TAVILY_API_KEY is not set in .env")
    else:
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": "HubSpot official developer documentation API",
                        "max_results": 2
                    }
                )
                if resp.status_code == 200:
                    hits = resp.json().get("results", [])
                    print(f"  ✅ PASS: Tavily Search API is active! (HTTP {resp.status_code})")
                    print(f"     Found {len(hits)} live documentation sources.")
                else:
                    print(f"  ❌ FAIL: Tavily returned HTTP {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"  ⚠️ ERROR connecting to Tavily: {e}")

    # 2. Test Google Gemini API
    print("\n[2/4] Checking Google Gemini AI Model...")
    if not gemini_key:
        print("  ❌ FAIL: GEMINI_API_KEY is not set in .env")
    else:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": "Return JSON with app: Stripe, category: Ecommerce, ready: true"}]}],
                "generationConfig": {"response_mime_type": "application/json"}
            }
            with httpx.Client(timeout=20) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    parsed = json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
                    print(f"  ✅ PASS: Google Gemini API ({gemini_model}) is active! (HTTP {resp.status_code})")
                    print(f"     Structured JSON extraction verified: {parsed}")
                else:
                    print(f"  ❌ FAIL: Gemini returned HTTP {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"  ⚠️ ERROR connecting to Google Gemini: {e}")

    # 3. Check Local Dashboard Files
    print("\n[3/4] Checking Local Deliverables...")
    output_html = os.path.exists("output/index.html")
    docs_html = os.path.exists("docs/index.html")
    apps_csv = os.path.exists("data/apps.csv")
    audit_csv = os.path.exists("data/audit.csv")

    if output_html and docs_html and apps_csv and audit_csv:
        print("  ✅ PASS: All deliverables exist and are in place:")
        print("     - output/index.html (Dashboard)")
        print("     - docs/index.html (GitHub Pages copy)")
        print("     - data/apps.csv (100 Apps)")
        print("     - data/audit.csv (Human Audit Log)")
    else:
        print("  ⚠️ Some deliverable files are missing.")

    # 4. Check GitHub Pages Status
    print("\n[4/4] Checking GitHub Pages Live Link...")
    pages_url = "https://rajshekharbind.github.io/integration-intelligence-agent/"
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            resp = client.get(pages_url)
            if resp.status_code == 200:
                print(f"  ✅ PASS: GitHub Pages is LIVE at: {pages_url}")
            else:
                print(f"  ⏳ PENDING (HTTP {resp.status_code}): GitHub Pages needs to be turned ON once in repository settings.")
                print("     To activate:")
                print("     1. Open: https://github.com/rajshekharbind/integration-intelligence-agent/settings/pages")
                print("     2. Source: Select 'Deploy from a branch' -> Branch: 'main', Folder: '/docs'")
                print("     3. Click 'Save'. It will be live in 60 seconds!")
    except Exception as e:
        print(f"  ⚠️ Error checking GitHub Pages: {e}")

    print("\n" + "=" * 60)
    print("  DIAGNOSTICS COMPLETE")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    run_diagnostics()
