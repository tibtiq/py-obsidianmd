default: sync format lint type

# list available just recipes
help:
    just --list

# sync environment with project dependencies
sync:
    uv sync

# update project dependencies
update:
    uv sync --upgrade

# run formatter
format:
    uvx ruff format .

# run linter
lint:
    uvx ruff check . --exclude test

# run type checker
type:
    uv run pyright .

# # run tests
# alias tests := test
# test target="": sync
#     #!/bin/bash
#     set -euo pipefail
#     IFS=$'\n\t'
#     target="{{ target }}"
#     if [ -z "$target" ]; then
#         uv run pytest -s ./tests
#     else
#         uv run pytest -s "$target"
#     fi
