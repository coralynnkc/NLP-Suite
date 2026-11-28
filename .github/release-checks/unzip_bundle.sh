#!/usr/bin/env bash
# unzip_bundle.sh <zip> <dest>: unpack a release zip; prints the NLP_Suite folder.
# Mac: ditto keeps the exec bits and symlinks the Mac zip relies on. Windows: 7z (on the runner).
set -euo pipefail
mkdir -p "$2"
if [ "$RUNNER_OS" = "macOS" ]; then ditto -x -k "$1" "$2"; else 7z x -y -o"$2" "$1" > /dev/null; fi
echo "$2/NLP_Suite"
