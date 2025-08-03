#!/bin/bash

# Download "mkdocs-site" from the "documentation.yml" workflow runs
# Script to be run on grass.osgeo.org
#
# (c) 2025, GPL 2+ Markus Neteler <neteler@osgeo.org>
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
# requires: jq, gh cli and login via gh auth login
###################################################################
# How this script works:
# - generate a new read-only token: https://github.com/settings/personal-access-tokens
# - cd to repo; login via gh auth login using the token
# - CAVEAT: these tokens expire after three months!
# - the last successful workflow run is identified via GH CLI
# - artifacts for this run are looked up
# - the artifact is downloaded as ZIP file (takes a moment)
#
# Useful GitHub CLI commands for debugging:
# - to find workflow names/IDs: gh workflow list
# - to preview runs: gh run list --workflow your-workflow.yml
# - to see artifact names: manually inspect a run on GitHub or use gh run view <run-id> --log
#
# Related docs:
# - GitHub CLI installation: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
# - GitHub CLI api: https://cli.github.com/manual/gh_api
# - GitHub workflow runs: https://docs.github.com/en/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-workflow

# === Configuration ===
OWNER="OSGeo"
REPO="grass"
REPO_LOCAL="$HOME/src/main/"
WORKFLOW_NAME="documentation.yml"  # or the workflow filename/id
ARTIFACT_NAME="mkdocs-site" # the name of the artifact
ZIP_OUTPUT="$ARTIFACT_NAME.zip"
OUTPUT_DIR="/tmp"

# === Script ===
# cleanup from previous run
cd $OUTPUT_DIR && rm -f $ZIP_OUTPUT

# this script must be run within the `grass` GH repo
echo "Changing into <$REPO_LOCAL>..."
cd $REPO_LOCAL

# use e.g. (read-only) TOKEN
# gh auth login

echo "Identifying last successful workflow run for '$WORKFLOW_NAME'..."

RUN_ID=$(gh run list \
  --branch main \
  --repo "$OWNER/$REPO" \
  --workflow "$WORKFLOW_NAME" \
  --status success \
  --limit 1 \
  --json databaseId \
  --jq '.[0].databaseId')

if [ -z "$RUN_ID" ]; then
  echo "ERROR: No successful workflow run found."
  exit 1
fi

echo "Found last successful run: $RUN_ID"
echo "Looking up artifacts for run $RUN_ID..."

ARTIFACT_ID=$(gh api \
  -H "Accept: application/vnd.github+json" \
  "/repos/$OWNER/$REPO/actions/runs/$RUN_ID/artifacts" \
  --jq ".artifacts[] | select(.name == \"$ARTIFACT_NAME\") | .id")

if [ -z "$ARTIFACT_ID" ]; then
  echo "Artifact '$ARTIFACT_NAME' not found in run $RUN_ID."
  exit 1
fi

echo "Found artifact ID: $ARTIFACT_ID"

echo "Downloading the artifact as ZIP (takes a moment)..."

gh api \
  -H "Accept: application/vnd.github+json" \
  -H "Accept: application/zip" \
  "/repos/$OWNER/$REPO/actions/artifacts/$ARTIFACT_ID/zip" \
  > "$OUTPUT_DIR/$ZIP_OUTPUT"

echo "Artifact saved as: $OUTPUT_DIR/$ZIP_OUTPUT"
