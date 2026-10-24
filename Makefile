SHELL := /bin/zsh
.DEFAULT_GOAL := help
.PHONY: test demo benchmark eval-hc3 help check push puhsb uv-build uv-publish uv-link

test:
	uv run --with pytest python -m pytest tests -q

demo:
	uv run lynote-ai examples/sample_ai_like.txt

benchmark:
	uv run python scripts/benchmark.py --markdown docs/BENCHMARK.md

eval-hc3:
	uv run python scripts/evaluate_hc3.py --markdown docs/HC3_EVALUATION.md

help:
	@echo "test demo benchmark eval-hc3 check push puhsb uv-build uv-publish uv-link"

check: test
	uv run python -m compileall -q src

push:
	@set -e; branch=$$(git branch --show-current); for remote in github gitlab; do git push "$$remote" "$$branch"; done

puhsb: push

uv-build:
	@if [ -d dist ]; then rm dist; fi
	uv build --no-sources

uv-publish: uv-build
	uv publish dist/*

uv-link:
	uv tool install --editable . --force
