#!/bin/bash
set -e
BAMF_DESKTOP_FILE_HINT=/var/lib/snapd/desktop/applications/logseq_logseq.desktop
notify-send "required s3 sync before opening logseq" -i /snap/logseq/11/app/resources/app/icon.png
/bin/bash /usr/local/bin/s3_sync.sh
/snap/bin/logseq %U