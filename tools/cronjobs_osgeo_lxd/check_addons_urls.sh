#!/bin/sh

# Tomas Zigo, 2020

# This script check compiled Add-Ons html manual pages for existence
# correct source and commits URL

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "usage: $0 addons_docs_html_dir_path, log_file_path \
log_html_file_path"
    echo "eg. $0 ~/.grass7/addons/docs/html \
~/.grass7/addons/logs/index_manual_pages.log \
~/.grass7/addons/logs/index_manual_pages.html"
    exit 1
fi

ADDONS_DOCS_HTML_DIR_PATH=$1
LOG_FILE_PATH=$2
LOG_HTML_FILE_PATH=$3

SRC_URL_ID="tree"
COMMITS_URL_ID="commits"

NORMAL_COLOR=$(tput sgr0)
RED_COLOR=$(tput setaf 1)

check_addon_html_manual_page() {
    for i in "${!urls[@]}"; do
        IFS=':'
        read -a template_page_url <<< "${urls[$i]}"

        found_urls=$(grep -woe "$SRC_URL_ID" <<< "${urls[$i]}" \
                          -woe "$COMMITS_URL_ID" <<< "${urls[$i]}" | wc -l)
        pgm=$(basename "${template_page_url[0]}")
        echo "<tr><td><tt>$pgm</tt></td>" \
             >> "$LOG_HTML_FILE_PATH"
        if [ "$found_urls" -eq 2 ]; then
            # Stdout, log file
            echo "${NORMAL_COLOR}Checking $pgm... \
source and commits URL: CORRECT" | tee -a "$LOG_FILE_PATH"
            # Html file
            echo "<td style=\"background-color: green\">\
source and commits URL: CORRECT</td>" >> "$LOG_HTML_FILE_PATH"
        else
            # Stdout, log file
            echo "${RED_COLOR}Checking $pgm... source or \
commits URL: INCORRECT" | tee -a "$LOG_FILE_PATH"
            # Html file
            echo "<td style=\"background-color: red\">\
source or commits URL: INCORRECT</td>" >> "$LOG_HTML_FILE_PATH"
        fi;
        tput sgr0
   done;
}

manual_html_pages=$(find "$ADDONS_DOCS_HTML_DIR_PATH" -type f \
                         -regex ".*.html" | sort | \
                        xargs grep -H "Available at:")

echo "${manual_html_pages}" | \
    { IFS=$'\n' read -rd '' -a urls; check_addon_html_manual_page; }

exit 0
