#!/bin/bash
set -euo pipefail
export TOKENIZERS_PARALLELISM=false
export HF_HUB_DISABLE_PROGRESS_BARS=1
PYTHONPATH=python python -m clipfix.main "$@"
