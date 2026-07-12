#!/bin/bash

# This script compiles GRASS GIS addons discovered across multiple GitHub
# repositories tagged with the topic "grass-gis-addons".
#
# Markus Neteler, 2022-2026
# based on https://github.com/OSGeo/grass-addons/blob/grass8/utils/cronjobs_osgeo_lxd/compile_addons_git.sh
# generalization supported by opencode.ai tool, OpenCode Zen (DeepSeek V4 Flash Free)
#
# Usage:
#   bash compile_addons_git.sh
#
# Requirements:
#   - GitHub CLI (gh) installed and authenticated
#     See: https://cli.github.com/
#   - git (SSH key configured for private repos)
#   - pip packages as needed by individual addons (see requirements.txt)
#   - wget
#
# The script:
#   1. Queries GitHub for all public repos with topic "grass-gis-addons"
#      (excluding OSGeo/grass-addons itself)
#   2. Clones each repo into a temporary directory
#   3. Discovers addon directories (those containing a Makefile)
#   4. Copies them into a consolidated source tree
#   5. Compiles each addon
#   6. Generates an HTML index of manual pages with source repo info
#
# Note: GitHub API has a rate limit of 60 unauthenticated requests/hour.
#       Authenticated (gh auth login) raises this to 5000/hour.

#### fail on error
# set -e

#### variables
GRASSSTARTBIN=grass

# Default values
ADDONBINPATH="$HOME/.grass8/addons"      # target dir for compiled addon binaries
ADDONMANPATH="$ADDONBINPATH/all_docs"    # target dir for generated addon manual pages
ALLADDONSSRC="/tmp/grass_addons"               # consolidated src tree of all addons
WORKDIR_REPOS="/tmp/grass_addons_repos"        # cloned repos before consolidation
CACHEDIR="$HOME/.cache/grass_addons_compiler"  # cache dir for checksums

# Overwrite default values if given
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -b|--addonbinpath) ADDONBINPATH="$2"; shift;;
    -m|--addonmanpath) ADDONMANPATH="$2"; shift;;
    -s|--alladdonssrc) ALLADDONSSRC="$2"; shift;;
    -w|--workdir)     WORKDIR_REPOS="$2"; shift;;
    -c|--cachedir)    CACHEDIR="$2"; shift;;
    --no-cache)       NOCACHE=1; shift;;
    *) echo -e "$1 not recognized as parameter. Aborting"; exit 1;;
  esac
  shift
done

echo "ADDONBINPATH is $ADDONBINPATH"
echo "ADDONMANPATH is $ADDONMANPATH"
echo "ALLADDONSSRC is $ALLADDONSSRC"
echo "WORKDIR_REPOS is $WORKDIR_REPOS"
echo "CACHEDIR is $CACHEDIR"
echo "NOCACHE is ${NOCACHE:-not set}"

# Parse version from GRASSBIN
GRASSBIN=$($GRASSSTARTBIN --config path)
VERSIONSTRING=$($GRASSSTARTBIN --config version)
GMAJOR=$(echo "$VERSIONSTRING" | cut -d'.' -f1)  # e.g. 8
GMINOR=$(echo "$VERSIONSTRING" | cut -d'.' -f2)  # e.g. 2
GPATCH=$(echo "$VERSIONSTRING" | cut -d'.' -f3)  # e.g. 0
DOTVERSION=$GMAJOR.$GMINOR
VERSION=$GMAJOR$GMINOR
GVERSION=$GMAJOR
GRASSVERSION=$VERSION

MYTITLE="GRASS GIS ${GMAJOR} Addons Manual pages available outside of the 'grass-addons' repository"

# launch dir
MYPWD=$(pwd)

########################################################################
# Step 1: Discover GitHub repos with topic "grass-gis-addons"
########################################################################
echo ""
echo "=============================================================="
echo "Step 1: Discovering GitHub repos with topic 'grass-gis-addons'"
echo "=============================================================="

# Find the real GitHub CLI (gh) — avoid shadowing by other tools
GH_BIN=""
for candidate in /usr/bin/gh /usr/local/bin/gh /snap/bin/gh; do
  if [ -x "$candidate" ]; then
    GH_BIN="$candidate"
    break
  fi
done
# Also check PATH, but verify it's the real GitHub CLI via --version
if [ -z "$GH_BIN" ]; then
  CANDIDATE=$(command -v gh 2>/dev/null || true)
  if [ -n "$CANDIDATE" ] && "$CANDIDATE" --version 2>/dev/null | grep -q "gh version"; then
    GH_BIN="$CANDIDATE"
  fi
fi

if [ -z "$GH_BIN" ]; then
  echo "ERROR: GitHub CLI (gh) is required. Install from https://cli.github.com/"
  exit 1
fi
echo "Using GitHub CLI: $GH_BIN"

# Query GitHub for repos with the topic "grass-gis-addons"
echo "Querying GitHub API for repos with topic 'grass-gis-addons'..."
REPO_JSON=$("$GH_BIN" search repos --topic "grass-gis-addons" \
  --json name,owner,url,description \
  --limit 1000 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$REPO_JSON" ]; then
  echo "ERROR: Failed to query GitHub. Check your 'gh' authentication."
  echo "Run '$GH_BIN auth login' and try again."
  exit 1
fi

# Parse JSON to get repo list, excluding OSGeo/grass-addons
REPO_LIST=$(echo "$REPO_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data:
    full_name = r['owner']['login'] + '/' + r['name']
    if full_name != 'OSGeo/grass-addons':
        print(full_name)
")

echo "Found repos (excluding OSGeo/grass-addons):"
echo "$REPO_LIST"
echo ""

if [ -z "$REPO_LIST" ]; then
  echo "No repos found. Aborting."
  exit 1
fi

# Save repo list for later use in HTML generation
echo "$REPO_LIST" > /tmp/gh_grass_addons_repos.csv

########################################################################
# Step 2: Clone repos and consolidate addon sources
########################################################################
echo ""
echo "=============================================================="
echo "Step 2: Cloning repos and consolidating addon source trees"
echo "=============================================================="

# Load compilation cache (persists across runs)
ADDON_CACHE_FILE="$CACHEDIR/addon_cache.json"
mkdir -p "$CACHEDIR"
if [ -f "$ADDON_CACHE_FILE" ]; then
  echo "Loaded compilation cache from $ADDON_CACHE_FILE"
else
  echo "{}" > "$ADDON_CACHE_FILE"
fi

# Cleanup consolidated source tree (always fresh — addon detection logic changes)
test -d "$ALLADDONSSRC" && rm -rf "$ALLADDONSSRC"
mkdir -p "$ALLADDONSSRC"
# Keep repo clones between runs for faster re-runs
mkdir -p "$WORKDIR_REPOS"

# Track which addon comes from which repo
ADDON_REPO_MAPPING="$ALLADDONSSRC/addon_to_repo.csv"
echo "addon,repo" > "$ADDON_REPO_MAPPING"

# Clone/Pull each repo
REPO_COUNT=0
while IFS= read -r repo; do
  [ -z "$repo" ] && continue
  REPO_COUNT=$((REPO_COUNT + 1))
  echo ""
  echo "--- Processing repo $REPO_COUNT: $repo ---"

  # Determine clone URL
  CLONE_URL="https://github.com/${repo}.git"

  # Create a sanitized directory name from the repo name
  REPO_DIR=$(echo "$repo" | tr '/' '_')
  CLONE_PATH="$WORKDIR_REPOS/$REPO_DIR"

  # Use cached clone if available, otherwise fresh clone
  if [ -d "$CLONE_PATH/.git" ]; then
    echo "Updating existing clone at $CLONE_PATH ..."
    git -C "$CLONE_PATH" pull --ff-only 2>/dev/null
    if [ $? -ne 0 ]; then
      echo "WARNING: Failed to update $repo. Will try fresh clone."
      rm -rf "$CLONE_PATH"
      git clone --depth 1 "$CLONE_URL" "$CLONE_PATH" 2>/dev/null || {
        echo "WARNING: Failed to clone $repo. Skipping."
        continue
      }
    fi
  else
    echo "Cloning $CLONE_URL into $CLONE_PATH ..."
    git clone --depth 1 "$CLONE_URL" "$CLONE_PATH" 2>/dev/null || {
      echo "WARNING: Failed to clone $repo. Skipping."
      continue
    }
  fi

  # ---------------------------------------------------------------
  # Discover addon directories within the cloned repo
  #
  # Strategy:
  #   a) If the repo root has Makefile with module prefix pattern
  #      (e.g. r.skyline/, v.clean.x/) => multi-addon repo, each
  #      subdirectory is an addon.
  #   b) If the repo root IS an addon (has a Makefile referencing
  #      MODULE_TOPDIR) => single-addon repo, copy root as addon
  #      named after the repo.
  #   c) If there's a subdirectory like src/ or grass-addons/ that
  #      contains addon dirs, descend into it.
  # ---------------------------------------------------------------

  # Helper: given a directory, list all addon subdirs within it
  find_addons_in_dir() {
    local searchdir="$1"
    local parent_repo="$2"
    local prefix="$3"   # optional prefix for addon name

    # Look for directories containing a Makefile
    find "$searchdir" -maxdepth 2 -name Makefile 2>/dev/null | while IFS= read -r mkf; do
      local addon_dir
      addon_dir=$(dirname "$mkf")
      local addon_name
      addon_name=$(basename "$addon_dir")

      # Skip non-addon dirs (e.g. testsuite/, docs/, etc.)
      case "$addon_name" in
        testsuite|docs|html|man|bin|scripts|etc|.git|__pycache__|*.png|*.css|*.svg)
          continue;;
      esac

      # Check if this looks like a GRASS addon (Makefile references MODULE_TOPDIR or has typical patterns)
      if grep -q "MODULE_TOPDIR" "$mkf" 2>/dev/null || grep -q "^PGM" "$mkf" 2>/dev/null; then
        local dest_name
        if [ -n "$prefix" ]; then
          dest_name="${prefix}_${addon_name}"
        else
          dest_name="$addon_name"
        fi
        echo "$addon_dir|$dest_name"
      fi
    done
  }

  FOUND_ADDONS=0

  # Strategy a: Check if repo root has Makefile (single-addon repo)
  if [ -f "$CLONE_PATH/Makefile" ]; then
    # Check if root Makefile defines PGM or references MODULE_TOPDIR
    # (skip cookiecutter templates which contain {{ }} placeholders)
    if ! grep -q "{{" "$CLONE_PATH/Makefile" 2>/dev/null && \
       (grep -q "^PGM\b" "$CLONE_PATH/Makefile" 2>/dev/null || \
        grep -q "^MODULE_TOPDIR" "$CLONE_PATH/Makefile" 2>/dev/null || \
        grep -q "MODULE_TOPDIR" "$CLONE_PATH/Makefile" 2>/dev/null); then
      # Repo root itself is an addon
      ADDON_NAME=$(basename "$repo" | sed 's/^grass-\?//' | sed 's/^[._-]*//')
      # Try to extract PGM from Makefile
      PGM=$(grep "^PGM" "$CLONE_PATH/Makefile" 2>/dev/null | head -1 | sed 's/^PGM\s*:=\s*//' | sed 's/^PGM\s*=\s*//' | tr -d '[:space:]')
      if [ -n "$PGM" ]; then
        ADDON_NAME="$PGM"
      fi
      # Copy the addon
      mkdir -p "$ALLADDONSSRC/$ADDON_NAME"
      cp -r "$CLONE_PATH"/* "$ALLADDONSSRC/$ADDON_NAME/" 2>/dev/null
      # Remove .git if accidentally copied
      rm -rf "$ALLADDONSSRC/$ADDON_NAME/.git" 2>/dev/null
      echo "  -> Single-addon repo: addon '$ADDON_NAME' from $repo"
      echo "$ADDON_NAME,$repo" >> "$ADDON_REPO_MAPPING"
      FOUND_ADDONS=$((FOUND_ADDONS + 1))
    fi
  fi

  # If no addon found at root, search subdirectories
  if [ $FOUND_ADDONS -eq 0 ]; then
    # Strategy b: Look for common subdirectories like src/, grass-addons/,
    #             or subdirs directly containing addon Makefiles

    # List of directories to search
    SEARCH_DIRS=("$CLONE_PATH")
    for sub in src grass-addons grass grass_addons addons; do
      [ -d "$CLONE_PATH/$sub" ] && SEARCH_DIRS+=("$CLONE_PATH/$sub")
    done

    for searchdir in "${SEARCH_DIRS[@]}"; do
      [ ! -d "$searchdir" ] && continue
      echo "  Searching $searchdir for addon Makefiles ..."

      # Find directories with Makefiles at depth 2 (so: subdir/Makefile)
      while IFS= read -r mkf; do
        addon_dir=$(dirname "$mkf")
        addon_name=$(basename "$addon_dir")

        # Skip non-addon dirs
        case "$addon_name" in
          testsuite|docs|html|man|bin|scripts|etc|.git|__pycache__|lib)
            continue;;
        esac

        # Verify it's a real addon Makefile (skip cookiecutter templates)
        if (grep -q "MODULE_TOPDIR" "$mkf" 2>/dev/null || grep -q "^PGM" "$mkf" 2>/dev/null) && \
           ! grep -q "{{" "$mkf" 2>/dev/null; then
          # Check if already copied (from another search dir)
          if [ -f "$ALLADDONSSRC/$addon_name/Makefile" ]; then
            echo "  WARNING: '$addon_name' already exists, skipping duplicate from $searchdir"
            continue
          fi
          mkdir -p "$ALLADDONSSRC/$addon_name"
          cp -r "$addon_dir"/* "$ALLADDONSSRC/$addon_name/" 2>/dev/null
          # Use PGM from Makefile as the mapping key (matches HTML filename)
          pgm=$(grep "^PGM" "$mkf" 2>/dev/null | head -1 | sed 's/^PGM\s*:=\s*//' | sed 's/^PGM\s*=\s*//' | tr -d '[:space:]')
          map_key="${pgm:-$addon_name}"
          echo "  -> Addon '$map_key' from $repo"
          echo "$map_key,$repo" >> "$ADDON_REPO_MAPPING"
          FOUND_ADDONS=$((FOUND_ADDONS + 1))
        fi
      done < <(find "$searchdir" -maxdepth 2 -name Makefile 2>/dev/null)
    done
  fi

  if [ $FOUND_ADDONS -eq 0 ]; then
    echo "  WARNING: No addons found in $repo"
  fi

done <<< "$REPO_LIST"

echo ""
echo "=============================================================="
echo "Consolidated addon sources in $ALLADDONSSRC"
echo "Addon-to-repo mapping written to $ADDON_REPO_MAPPING"
echo "=============================================================="

# Verify we have something to compile
ADDON_COUNT=$(find "$ALLADDONSSRC" -maxdepth 2 -name Makefile 2>/dev/null | wc -l)
if [ "$ADDON_COUNT" -eq 0 ]; then
  echo "ERROR: No addons found to compile. Aborting."
  exit 1
fi
echo "Found $ADDON_COUNT addon(s) to compile."

########################################################################
# Step 3: Compile addons
########################################################################
echo ""
echo "=============================================================="
echo "Step 3: Compiling addons"
echo "=============================================================="

PLATFORM="x86_64"
TOPDIR=${GRASSBIN}
ADDON_PATH=${ADDONBINPATH}
GRASS_STARTUP_PROGRAM=${GRASSSTARTBIN}
INDEX_FILE="index"
INDEX_MANUAL_PAGES_FILE="index_manual_pages"
ADDONS_PATHS_JSON_FILE="addons_paths.json"
SEPARATE=1

if [ ! -d "${ADDONBINPATH}" ]; then
  mkdir -p "${ADDONBINPATH}"
fi

# Generate temporary location (needed by g.extension -j and some addon Makefiles)
DEMOLOCATION="/tmp/grass_demolocation"
if [ ! -d "$DEMOLOCATION" ]; then
  echo "Generating demolocation at $DEMOLOCATION..."
  $GRASSSTARTBIN -c epsg:4326 "$DEMOLOCATION" -e 2>/dev/null || true
fi

if [ -n "$SEPARATE" ]; then
  SEP=1
else
  SEP=0
fi

# Only clean logs between runs (keep existing compiled addons for caching)
mkdir -p "$ADDON_PATH" "$ADDON_PATH/logs"
rm -f "$ADDON_PATH/logs/${INDEX_FILE}.html" "$ADDON_PATH/logs/${INDEX_MANUAL_PAGES_FILE}.html"
touch "$ADDON_PATH/logs/${INDEX_FILE}.log.txt"

cd "$ALLADDONSSRC" || exit 1

# Helper: compute a deterministic hash of an addon's source files
compute_addon_hash() {
  local addon_dir="$1"
  find "$addon_dir" -maxdepth 1 -type f \
    ! -name '.git' ! -name '*.pyc' ! -name '__pycache__' \
    -exec sha256sum {} + 2>/dev/null | sha256sum | cut -d' ' -f1
}

date=$(date -R)
uname=$(uname)

html_template="<!--<?xml-stylesheet href=\"style.css\" type=\"text/css\"?>-->
<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.1//EN\"
      \"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd\">

<html xmlns=\"http://www.w3.org/1999/xhtml\" xml:lang=\"en\" >

<head>
<meta http-equiv=\"Content-Type\" content=\"application/xhtml+xml; charset=utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>GRASS GIS AddOns Logs ($PLATFORM)</title>
<style type=\"text/css\">
h1 { font-size: 125%; font-weight: bold; }
table
{
border-collapse:collapse;
}
table,th, td
{
border: 1px solid black;
}
</style>
</head>
<body>
<h1>GRASS $GMAJOR Addons ($PLATFORM) / $uname (logs generated $date)</h1>
<hr />
<table cellpadding=\"5\">
<tr><th style=\"background-color: grey\">AddOns</th>
<th style=\"background-color: grey\">Status</th>"

# initiate the index file
echo "$html_template" > "$ADDON_PATH/logs/${INDEX_FILE}.html"
echo "<th style=\"background-color: grey\">Log file</th></tr>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"

echo "$html_template" > "$ADDON_PATH/logs/${INDEX_MANUAL_PAGES_FILE}.html"

echo "-----------------------------------------------------"
echo "Addons compiled into '$ADDON_PATH'..."
echo "-----------------------------------------------------"

MYPWD=$(pwd)

# loop over all addons
for m in $(ls -d */Makefile 2>/dev/null); do
  m="${m%%/Makefile}"
  # Skip invalid addon names (cookiecutter placeholders, hidden dirs, etc.)
  case "$m" in
    *\{\{*|*\}\}*|*cookiecutter*|\.*) echo "Skipping invalid addon: $m"; continue;;
  esac

  if [ $SEP -eq 1 ]; then
    path="$ADDON_PATH/$m"
  else
    path="$ADDON_PATH"
  fi

  # --- Compilation cache check ---
  addon_src_dir="$ALLADDONSSRC/$m"
  if [ -d "$path/bin" ] && [ -d "$path/docs/html" ] && [ -z "$NOCACHE" ]; then
    current_hash=$(compute_addon_hash "$addon_src_dir" 2>/dev/null)
    cached_hash=$(python3 -c "import json; d=json.load(open('$ADDON_CACHE_FILE')); print(d.get('$m',''))" 2>/dev/null)
    if [ "$current_hash" = "$cached_hash" ]; then
      echo "CACHED $m (source unchanged)"
      printf "%-30s%s\n" "$m" "SUCCESS" >> "$ADDON_PATH/logs/${INDEX_FILE}.log.txt"
      echo "<tr><td><tt>$m</tt></td><td style=\"background-color: green\">SUCCESS</td>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
      echo "<td><a href=\"$m.log.txt\">log</a></td></tr>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
      continue
    fi
  fi

  # --- Compile ---
  echo -n "Compiling $m..."
  cd "$m" || continue

  export GRASS_ADDON_BASE=$path
  if [ ! -d "$GRASS_ADDON_BASE" ]; then
    mkdir -p "$GRASS_ADDON_BASE"
  fi
  # Try download Add-Ons json file paths (non-critical, skip if it fails)
  if [ ! -f "$GRASS_ADDON_BASE/$ADDONS_PATHS_JSON_FILE" ] && [ ! -f "$(dirname "$GRASS_ADDON_BASE")/$ADDONS_PATHS_JSON_FILE" ]; then
    $GRASS_STARTUP_PROGRAM --tmp-project EPSG:4326 --exec g.extension -j 2>/dev/null || true
    if [ ! -f "$(dirname "$GRASS_ADDON_BASE")/$ADDONS_PATHS_JSON_FILE" ] && [ -f "$GRASS_ADDON_BASE/$ADDONS_PATHS_JSON_FILE" ]; then
      mv "$GRASS_ADDON_BASE/$ADDONS_PATHS_JSON_FILE" "$(dirname "$GRASS_ADDON_BASE")/$ADDONS_PATHS_JSON_FILE"
    fi
  fi
  echo "<tr><td><tt>$m</tt></td>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
  make MODULE_TOPDIR="$TOPDIR" clean > /dev/null 2>&1
  make MODULE_TOPDIR="$TOPDIR" \
    BIN="$path/bin" \
    HTMLDIR="$path/docs/html" \
    MANBASEDIR="$path/docs/man" \
    SCRIPTDIR="$path/scripts" \
    ETC="$path/etc" \
    SOURCE_URL="" \
    HTML_PAGE_FOOTER_PAGES_PATH="../" \
    > "$ADDON_PATH/logs/$m.log.txt" 2>&1
  make_ret=$?
  # Strip gcc generated ANSI escape codes from log file
  sed -i 's/\x1b\[[0-9;]*[a-zA-Z]//g' "$ADDON_PATH/logs/$m.log.txt"
  if [ $make_ret -eq 0 ]; then
    printf "%-30s%s\n" "$c/$m" "SUCCESS" >> "$ADDON_PATH/logs/${INDEX_FILE}.log.txt"
    echo " SUCCESS"
    echo "<td style=\"background-color: green\">SUCCESS</td>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
    # Update compilation cache
    current_hash=$(compute_addon_hash "$addon_src_dir" 2>/dev/null)
    python3 -c "
import json
d = json.load(open('$ADDON_CACHE_FILE'))
d['$m'] = '$current_hash'
json.dump(d, open('$ADDON_CACHE_FILE', 'w'))
" 2>/dev/null || true
  else
    printf "%-30s%s\n" "$c/$m" "FAILED" >> "$ADDON_PATH/logs/${INDEX_FILE}.log.txt"
    echo " FAILED"
    echo "<td style=\"background-color: red\">FAILED</td>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
  fi
  echo "<td><a href=\"$m.log.txt\">log</a></td></tr>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"
  cd ..
done

cd "$MYPWD" || exit 1
unset GRASS_ADDON_BASE

echo "</table><hr />
<div style=\"text-align: right\">Valid: <a href=\"http://validator.w3.org/check/referer\">XHTML</a></div>
</body></html>" >> "$ADDON_PATH/logs/${INDEX_FILE}.html"

echo "</table><hr />
<div style=\"text-align: right\">Valid: <a href=\"http://validator.w3.org/check/referer\">XHTML</a></div>
</body></html>" >> "$ADDON_PATH/logs/${INDEX_MANUAL_PAGES_FILE}.html"

echo "Log files written to <$ADDON_PATH/logs/index.html>"

# Collect list of currently detected addons (from source tree)
declare -A CURRENT_ADDONS
for m in $(ls -d "$ALLADDONSSRC"/*/Makefile 2>/dev/null); do
  m=$(basename "$(dirname "$m")")
  CURRENT_ADDONS["$m"]=1
done

# Remove stale addon dirs from ADDONBINPATH (those no longer in source tree)
for d in "$ADDONBINPATH"/*/; do
  dname=$(basename "$d")
  [ "$dname" = "logs" ] && continue
  [ -n "${CURRENT_ADDONS[$dname]+x}" ] && continue
  [ -d "$d" ] && rm -rf "$d" && echo "  Removed stale addon: $dname"
done

########################################################################
# Step 4: Generate addon manual pages overview HTML
########################################################################
echo ""
echo "=============================================================="
echo "Step 4: Generating manual pages overview"
echo "=============================================================="

# cleanup last run
test -d "$ADDONMANPATH" && rm -rf "$ADDONMANPATH"
mkdir -p "$ADDONMANPATH"

# Load the addon-to-repo mapping into an associative array for quick lookup
declare -A ADDON_REPO
if [ -f "$ADDON_REPO_MAPPING" ]; then
  while IFS=',' read -r addon repo; do
    [ -z "$addon" ] && continue
    ADDON_REPO["$addon"]="$repo"
  done < "$ADDON_REPO_MAPPING"
fi

# Fill in mapping gaps: sub-addons compiled by a parent Makefile (e.g.
# i.sentinel_2.autotraining from mundialis/i.sentinel_2) inherit the
# parent's repo. Scan all compiled addon dirs for extra HTML man pages.
for parent_dir in "$ADDONBINPATH"/*/; do
  parent_name=$(basename "$parent_dir")
  [ "$parent_name" = "logs" ] && continue
  parent_repo="${ADDON_REPO[$parent_name]}"
  [ -z "$parent_repo" ] && continue
  for htm in "$parent_dir/docs/html/"*.html; do
    [ ! -f "$htm" ] && continue
    mod=$(basename "$htm" .html)
    [ "$mod" = "$parent_name" ] && continue
    if [ -z "${ADDON_REPO[$mod]+x}" ]; then
      ADDON_REPO["$mod"]="$parent_repo"
      echo "  Mapped $mod -> $parent_repo (inherited from $parent_name)"
    fi
  done
done

# Copy all HTML manual pages into one directory
\cp "$ADDONBINPATH"/*/docs/html/*.html "$ADDONMANPATH" 2>/dev/null
\cp "$ADDONBINPATH"/*/docs/html/*.png "$ADDONMANPATH" 2>/dev/null

module_prefix() {
  case "$1" in
    "ace")
      label="actinia"
      anchor="a"
      ;;
    "db")
      label="Database"
      anchor="db"
      ;;
    "d")
      label="Display"
      anchor="d"
      ;;
    "exporter")
      label="exporter (actinia)"
      anchor="a"
      ;;
    "g")
      label="General"
      anchor="g"
      ;;
    "i")
      label="Imagery"
      anchor="i"
      ;;
    "importer")
      label="importer (actinia)"
      anchor="a"
      ;;
    "m")
      label="Miscellaneous"
      anchor="m"
      ;;
    "r")
      label="Raster"
      anchor="r"
      ;;
    "r3")
      label="3D raster"
      anchor="r3"
      ;;
    "v")
      label="Vector"
      anchor="v"
      ;;
    "t")
      label="Temporal"
      anchor="t"
      ;;
    "ps")
      label="Postscript"
      anchor="ps"
      ;;
    *)
      label="unknown"
      anchor="unknown"
      ;;
  esac
  echo "<a name=\"$anchor\"></a>"
  echo "<h3>$label</h3>"
}

generate() {
  major=$1
  minor=$2
  patch=$3
  manpath=$4

  cd "$manpath" || exit 1

  if test -f index.html; then
    \mv index.html index.html.bak
  fi

  LASTDATE=$(date +"%d %b %Y")

  echo "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">
<html>
<head>
 <title>GRASS GIS ${major}.${minor} Addons Manual pages</title>
 <meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">
 <meta name=\"Author\" content=\"GRASS Development Team\">
 <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
 <link rel=\"stylesheet\" href=\"grassdocs.css\" type=\"text/css\">
</head>
<body bgcolor=\"#FFFFFF\">
<h2>$MYTITLE</h2>

<table><tr><td>
<img src=\"https://grass.osgeo.org/images/logos/grass-logo/grass-gradient.svg\" width=200>
</td><td>
<a href=\"https://grass.osgeo.org\">GRASS GIS</a> is free software,
anyone may develop their own extensions (addons). The addons listed
here are currently not part of the core software package.<br>
Addons can easily be <b>installed</b> in your local GRASS GIS installation
through the graphical user interface (<i>Menu - Settings - Addons
Extension - Install</i>) or via the <a
href=\"https://grass.osgeo.org/grass-stable/manuals/g.extension.html\">g.extension</a> command.  <p> <i>These
manual pages are updated daily. Last run: $LASTDATE</i>
<p> How to contribute?
<p> See instructions here: <a href=\"https://github.com/mundialis/grass-gis-helpers/blob/main/How-to-create-a-GRASS-GIS-addon.md\">How to create a GRASS GIS addon</a>.
<p>
See also log files of compilation:
<a href=\"$ADDON_PATH/logs/index.html\">Linux log files</a>
<p>
The GRASS addons here are generated from the
<a href=\"https://github.com/topics/grass-gis-addons\">GitHub topic: grass-gis-addons</a>.

</tr></table>
<hr>
<div class=\"toc\">
<h4 class=\"toc\">Table of contents</h4>
<ul class=\"toc\">
<li class=\"toc\"><a class=\"toc\" href=\"#d\">Display commands (d.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#db\">Database commands (db.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#g\">General commands (g.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#i\">Imagery commands (i.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#m\">Miscellaneous commands (m.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#r\">Raster commands (r.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#r3\">3D raster commands (r3.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#t\">Temporal commands (t.*)</a></li>
<li class=\"toc\"><a class=\"toc\" href=\"#v\">Vector commands (v.*)</a></li>
</ul>
</div>" >> index.html

  prefix_last=""
  for currfile in $(ls -1 *.html 2>/dev/null | grep -v index.html); do
    # module prefix
    prefix=$(echo "$currfile" | cut -d'.' -f1)
    if [ -z "$prefix_last" ] || [ "$prefix" != "$prefix_last" ]; then
      if [ "$prefix_last" != "" ]; then
        echo "</ul>" >> index.html
      fi
      module_prefix "$prefix" >> index.html
      echo "<ul>" >> index.html
      prefix_last=$prefix
    fi

    module=$(echo "$currfile" | sed 's+\.html$++g')
    echo "<li style=\"margin-left: 20px\"><a href=\"$currfile\">$module</a>: " >> index.html

    # Extract description from the first <meta name="description"> tag in the manual page
    if [ -f "$currfile" ]; then
      desc=$(grep -i '<meta.*name="description"' "$currfile" 2>/dev/null | \
             sed 's/.*content="//' | sed 's/".*//' | head -1)
      if [ -n "$desc" ]; then
        echo "$desc" >> index.html
      fi
    fi

    # Annotate with source repository
    sourcerepo="${ADDON_REPO[$module]}"
    if [ -z "$sourcerepo" ]; then
      sourcerepo="unknown"
    fi
    echo " <font color=\"#AAAAAA\">(repo: <a href=\"https://github.com/$sourcerepo\">$sourcerepo</a>)</font>" >> index.html

    # check if testsuite is present
    if test -d "$ALLADDONSSRC/$module/testsuite"; then
      echo "<font color=\"#AAAAAA\">[testsuite: </font><font color=\"#77FF77\">yes</font><font color=\"#AAAAAA\">]</font>" >> index.html
    else
      if test -d "$ALLADDONSSRC/$module/"*/testsuite 2>/dev/null; then
        echo "<font color=\"#AAAAAA\">[testsuite: </font><font color=\"#77FF77\">yes</font><font color=\"#AAAAAA\">]</font>" >> index.html
      else
        echo "<font color=\"#AAAAAA\">[testsuite: </font><font color=\"#FF7777\">no</font><font color=\"#AAAAAA\">]</font>" >> index.html
      fi
    fi

    echo "" >> index.html
  done

  ADDONCOUNT=$(grep "margin-left" index.html | wc -l)
  echo "<p>
<hr>
Found $ADDONCOUNT addons
<p>" >> index.html

  year=$(date +%Y)
  echo "</ul><hr>
&copy; 2015-${year} <a href=\"https://grass.osgeo.org\">GRASS Development Team</a>, $MYTITLE<br>" >> index.html
  echo "<i><small>$(date -u)</small></i>" >> index.html
  echo "</body></html>" >> index.html
  rm -f index.html.bak
}

# Generate the index
generate "$GMAJOR" "$GMINOR" "$GPATCH" "$ADDONMANPATH"

# Fetch supporting files
(cd "$ADDONMANPATH" || exit 1;
  # Download and convert logo SVG to PNG for manual page footer
  wget --quiet -N https://grass.osgeo.org/images/logos/grass-logo/grass-gradient.svg -O grass_logo.svg 2>/dev/null
  if command -v convert &>/dev/null; then
    convert grass_logo.svg grass_logo.png 2>/dev/null
  elif command -v rsvg-convert &>/dev/null; then
    rsvg-convert grass_logo.svg -o grass_logo.png 2>/dev/null
  else
    echo "  WARNING: no SVG-to-PNG converter found (install ImageMagick or librsvg)"
  fi
  wget --quiet -N https://grass.osgeo.org/grass-stable/manuals/grassdocs.css 2>/dev/null
  wget --quiet -N https://grass.osgeo.org/grass-stable/manuals/hamburger_menu_close.svg 2>/dev/null
  wget --quiet -N https://grass.osgeo.org/grass-stable/manuals/hamburger_menu.svg 2>/dev/null
)



echo ""
echo "=============================================================="
echo "Done!"
echo "Manual pages:  ${ADDONMANPATH}/index.html"
echo "Log files:     ${ADDON_PATH}/logs/index.html"
echo "=============================================================="

exit 0
