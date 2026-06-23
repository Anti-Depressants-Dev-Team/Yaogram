#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runner="${repo_root}/scripts/run_local_tests.py"

build=0
verify_build=0
config="Debug"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)
            build=1
            shift
            ;;
        --verify-build)
            verify_build=1
            shift
            ;;
        --config)
            config="${2:-}"
            if [[ -z "$config" ]]; then
                echo "--config requires a value" >&2
                exit 2
            fi
            shift 2
            ;;
        -h|--help)
            exec python3 "$runner" --help
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

args=()
if [[ "$build" -eq 1 ]]; then
    args+=(--build)
fi
if [[ "$verify_build" -eq 1 ]]; then
    args+=(--verify-build)
fi
if [[ "$config" != "Debug" ]]; then
    args+=(--config "$config")
fi

exec python3 "$runner" "${args[@]}"
