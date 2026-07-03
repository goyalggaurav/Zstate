#!/usr/bin/env bash
# CI parity (P3-39) — the single source of truth for what CI runs.
# .github/workflows/ci.yml executes this script; run it locally before pushing.
set -euo pipefail
cd "$(dirname "$0")/.."

# Match CI: no live API calls.
export OPENAI_API_KEY=""
export ANTHROPIC_API_KEY=""
export GEMINI_API_KEY=""

echo "== Python: $(python3 --version)"
python3 - <<'EOF'
import sys
if sys.version_info[:2] != (3, 14):
    print(f"WARN: CI pins Python 3.14; you are on {sys.version.split()[0]}", file=sys.stderr)
EOF

echo "== Smoke test"
python3 scripts/smoke_test.py

echo "== Manifest validator"
python3 benchmark_v0.1/scripts/validate_manifest.py

echo "== Publish gates (manifest-driven)"
for task in $(python3 - <<'EOF'
import sys
sys.path.insert(0, "benchmark_v0.1/scripts")
from task_registry import published_task_ids
print("\n".join(published_task_ids()))
EOF
); do
  echo "-- $task"
  python3 benchmark_v0.1/scripts/validate_publish_task.py --task "$task"
done

echo "== Schema coherence (P3-37)"
python3 benchmark_v0.1/scripts/validate_task_schema_coherence.py --all

echo "== Doc sync check"
python3 benchmark_v0.1/scripts/sync_track_a_docs.py --check

echo "== Leaderboard from pinned campaign report"
python3 benchmark_v0.1/scripts/generate_leaderboard.py

echo "== CI parity: all steps passed"
