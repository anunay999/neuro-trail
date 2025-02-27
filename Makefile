.PHONY: lint-docs format-docs clean-docs codespell

format-docs:
	uv run ruff format ./docs
	uv run ruff check --fix ./docs

format:
	uv run ruff format ./src
	uv run ruff check --fix ./src

lint:
	uv run ruff format --check ./src
	uv run ruff check ./src

# Check the docs for linting violations
lint-docs:
	uv run ruff format --check docs/
	uv run ruff check docs/

	uv run ruff format --check docs/
	uv run ruff check docs/