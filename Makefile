.PHONY: lint-docs format-docs clean-docs codespell

format-docs:
	uv run ruff format ./docs
	uv run ruff check --fix ./docs

format:
	uv run ruff format ./backend
	uv run ruff check --fix ./backend
	uv run ruff format ./frontend
	uv run ruff check --fix ./frontend

lint:
	uv run ruff format --check ./backend
	uv run ruff format --check ./frontend
	uv run ruff check ./backend
	uv run ruff check ./frontend

# Check the docs for linting violations
lint-docs:
	uv run ruff format --check docs/
	uv run ruff check docs/

	uv run ruff format --check docs/
	uv run ruff check docs/