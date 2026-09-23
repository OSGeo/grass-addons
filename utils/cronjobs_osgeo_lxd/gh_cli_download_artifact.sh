#!/bin/bash

# Download "mkdocs-site" from the "documentation.yml" workflow runs
# Script to be run on grass.osgeo.org
#
# (c) 2025-2026, GPL 2+ Markus Neteler <neteler@osgeo.org>
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
# requires: jq, gh cli and login via gh auth login
###################################################################
# How this script works:
# - generate a new read-only token: https://github.com/settings/personal-access-tokens
# - activate token on target server which runs this script (see below): gh auth login
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

# branch parameter: "main" or "releasebranch_8_5"

MYBRANCH=$1
[ -z "$MYBRANCH" ] && MYBRANCH="main"

# === Configuration ===
OWNER="OSGeo"
REPO="grass"
#
REPO_LOCAL="$HOME/src/$MYBRANCH/"       # e.g., neteler@grasslxd:~/src/main/ or ~/src/releasebranch_8_5/
WORKFLOW_NAME="documentation.yml"  # or the workflow filename/id
ARTIFACT_NAME="mkdocs-site" # the name of the artifact
ZIP_OUTPUT="${MYBRANCH}.zip"  # must match the path expected by fetch_unpack_manual_GHA.sh
# per-user directory: the job runs as different users (neteler, grassbot, ...)
# and a shared /tmp path lets one user's leftover file block another user's run
OUTPUT_DIR="${OUTPUT_DIR:-${TMPDIR:-/tmp}/grass_manuals_${USER}}"

# === Script ===
# cleanup from previous run
mkdir -p "$OUTPUT_DIR" || exit 1
cd "$OUTPUT_DIR" || exit 1
rm -f "$ZIP_OUTPUT"

# this script must be run within the `grass` GH repo
echo "Changing into <$REPO_LOCAL>..."
cd "$REPO_LOCAL" || exit 1

# use GitHub read-only TOKEN
# cd src/main/
# gh auth login
# answers:
#  Where do you use GitHub? GitHub.com
#  What is your preferred protocol for Git operations on this host? HTTPS
#  How would you like to authenticate GitHub CLI? Paste an authentication token

echo "Identifying last successful workflow run for '$WORKFLOW_NAME'..."

RUN_ID=$(gh run list \
  --branch "$MYBRANCH" \
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

if ! gh api \
  -H "Accept: application/vnd.github+json" \
  -H "Accept: application/zip" \
  "/repos/$OWNER/$REPO/actions/artifacts/$ARTIFACT_ID/zip" \
  > "$OUTPUT_DIR/$ZIP_OUTPUT"; then
  echo "ERROR: Failed to download artifact $ARTIFACT_ID (it may have expired)."
  rm -f "$OUTPUT_DIR/$ZIP_OUTPUT"
  exit 1
fi

# verify that the downloaded file is a valid ZIP (catches truncated
# downloads and API error bodies saved as file content)
if ! unzip -tq "$OUTPUT_DIR/$ZIP_OUTPUT" > /dev/null; then
  echo "ERROR: Downloaded file <$OUTPUT_DIR/$ZIP_OUTPUT> is not a valid ZIP archive."
  rm -f "$OUTPUT_DIR/$ZIP_OUTPUT"
  exit 1
fi

echo "Artifact saved as: $OUTPUT_DIR/$ZIP_OUTPUT"
