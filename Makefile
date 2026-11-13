.PHONY: install check test verify report lock audit

install:
	python -m venv .venv && .venv/bin/pip install -e ".[dev]"

check:
	ruff check . && ruff format --check . && mypy && pytest --cov=govpack --cov-fail-under=85

test:
	pytest

verify:
	govpack check --fail-on low && govpack report --check

# Needs the evidence repositories checked out side by side; see docs/runbooks/evidence-drift.md
lock:
	govpack lock --repos $(REPOS)

report:
	govpack report

audit:
	pip-audit --skip-editable
