#!/bin/bash
# a status print for productivity things

status () {

    set -e
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    NORMAL=$(tput sgr0)
    STATUS_PATH=${HOME}/.status
    while IFS="" read -r p || [ -n "$p" ]
    do
    VALUE="${p%%\=*}"
    STAMP="${p#*\=}"
    if [[ $STAMP == '' ]]; then
        SINCE="${RED}Never${NORMAL}"
    else
        SINCE_VAL=$(( ($(date +%s) - $(date --date=$STAMP "+%s")) / 60 ))
        if [[ $SINCE_VAL -gt 60 ]]; then
            SINCE="${RED}$(( $SINCE_VAL / 60 )) hours ago${NORMAL}"
        else
            SINCE="${GREEN}$SINCE_VAL minutes ago${NORMAL}"
        fi
    fi
    printf '%s\n' "$VALUE: $SINCE"
    done < $STATUS_PATH
}