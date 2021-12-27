#!/bin/bash

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

# Colour output text
if [ $# -eq 3 ]; then
    COLOR_OUTPUT=1
else
    case $4 in
        ''|*[!0-9]*)
            if [[ "$4" == [tT][rR][uU][eE] ]] || [[ "$4" == [yY][eE][sS] ]]; then
                COLOR_OUTPUT=0
            else
                COLOR_OUTPUT=1
            fi
            ;;
        *)
            if [ "$4" -eq 0 ]; then
                COLOR_OUTPUT=0
            else
                COLOR_OUTPUT=1
            fi
           ;;
    esac
fi

ADDONS_DOCS_HTML_DIR_PATH=$1
LOG_FILE_PATH=$2
LOG_HTML_FILE_PATH=$3

# Addon source code and histrory URL
URL_TREE_COMMITS="tree|commits"

NORMAL_COLOR=$(tput sgr0)
RED_COLOR=$(tput setaf 1)

check_addon_html_manual_page() {
    for i in "${!urls[@]}"; do
        IFS=':'
        read -a template_page_url <<< "${urls[$i]}"
        found_urls=$(egrep -woe $URL_TREE_COMMITS $template_page_url | wc -l)
        pgm=$(basename "${template_page_url[0]}")
        echo "<tr><td><tt>$pgm</tt></td>" \
             >> "$LOG_HTML_FILE_PATH"
        if [ "$found_urls" -eq 2 ]; then
            if [ "$COLOR_OUTPUT" -eq 0 ]; then
                # Stdout, log file
                echo "${NORMAL_COLOR}Checking $pgm... \
source and commits URL: CORRECT" | tee -a "$LOG_FILE_PATH"
            else
                echo "Checking $pgm... \
source and commits URL: CORRECT" | tee -a "$LOG_FILE_PATH"
            fi
            # Html file
            echo "<td style=\"background-color: green\">\
source and commits URL: CORRECT</td>" >> "$LOG_HTML_FILE_PATH"
        else
            if [ "$COLOR_OUTPUT" -eq 0 ]; then
                # Stdout, log file
                echo "${RED_COLOR}Checking $pgm... source or \
commits URL: INCORRECT" | tee -a "$LOG_FILE_PATH"
            else
                echo "Checking $pgm... source or \
commits URL: INCORRECT" | tee -a "$LOG_FILE_PATH"
            fi
            # Html file
            echo "<td style=\"background-color: red\">\
source or commits URL: INCORRECT</td>" >> "$LOG_HTML_FILE_PATH"
        fi;
        if [ "$COLOR_OUTPUT" -eq 0 ]; then tput sgr0; fi
   done;
}

manual_html_pages=$(find "$ADDONS_DOCS_HTML_DIR_PATH" -type f \
                         -regex ".*.html" | sort | \
                        xargs grep -H "Available at:")

echo "${manual_html_pages}" | \
    { IFS=$'\n' read -rd '' -a urls; check_addon_html_manual_page; }

exit 0
