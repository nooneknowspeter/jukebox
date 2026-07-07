default:
    @just --list

format args="":
    treefmt {{ args }} --config-file ./treefmt.toml

lint args="":
    treefmt {{ args }} --config-file ./treefmt.lint.toml

generate-all:
    uv run python main.py generate

list-themes:
    uv run python main.py list

screenshots:
    uv run python main.py screenshot

cover-art theme:
    uv run python main.py cover {{ theme }}
