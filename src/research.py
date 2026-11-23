"""
Entrypoint for research run: python -m src.research
"""
import sys
from src.research_agent import run_pipeline

if __name__ == "__main__":
    force = "--force" in sys.argv
    limit = None
    for idx, arg in enumerate(sys.argv):
        if arg == "--limit" and idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    run_pipeline(limit=limit, force=force)
