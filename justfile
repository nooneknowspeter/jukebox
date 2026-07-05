default:
    @just --list

format args="":
    treefmt {{ args }} --config-file ./treefmt.toml

lint args="":
    treefmt {{ args }} --config-file ./treefmt.lint.toml
