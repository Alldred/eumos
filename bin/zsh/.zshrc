# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Stuart Alldred. All Rights Reserved

# Jump to SLATE_ROOT
cd $SLATE_ROOT

# Custom prompt to make it clear this is the slate environment
PROMPT="[SLATE]:$PROMPT"

# Inherit the user history location
export HISTFILE=$USER_HISTFILE

# Incrementally append to history file
setopt INC_APPEND_HISTORY

# Ensure UV environment is installed
if [ ! -d ".venv" ]; then
    echo "# Creating virtual environment with UV"
    uv venv .venv
fi

# Activate the UV virtual environment
source .venv/bin/activate

# Sync dependencies with UV
if [ -f "pyproject.toml" ]; then
    echo "# Syncing dependencies with UV"
    uv sync
fi

# Install pre-commit
echo "# Setting up pre-commit hooks"
pre-commit install > /dev/null
