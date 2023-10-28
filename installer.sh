#!/bin/bash
set -e
if [[ "$1" == "s3_sync" ]]; then
    echo "setting up s3 sync"
    SETTINGS_PATH=${HOME}/.productivity_porn_settings
    cp -u .productivity_porn_settings.template $SETTINGS_PATH
    read -p "please configure your ${SETTINGS_PATH} file. Is your file updated?: [y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export $(cat ${SETTINGS_PATH} | xargs) 1> /dev/null
        echo ""
    else
        echo "OK aborting s3 sync install."
        exit 0
    fi
    cp -u .personal_secrets.template $PERSONAL_SECRETS_PATH
    read -p "please configure your ${PERSONAL_SECRETS_PATH} file. Is your file updated?: [y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        printf "\ngreat!"
    else
        printf "\nOK aborting s3 sync install."
        exit 0
    fi
    printf "\ninstalling s3_sync.sh to /usr/local/bin. (this will require sudo)..."
    sudo cp s3_sync/s3_sync.sh /usr/local/bin/s3_sync.sh
    printf "\ninstalled."

    CRONLINE="*/${S3_SYNC_LAG_MINUTES} * * * * HOME=${HOME} /bin/bash /usr/local/bin/s3_sync.sh"
    printf "\nattempting to add ${CRONLINE} to crontab...\n"
    if [[ $(crontab -l | egrep -v "^(#|$)" | grep -q '/bin/bash /usr/local/bin/s3_sync.sh'; echo $?) == 1 ]]; then
        printf "\ns3 sync not in crontab. adding...\n"
        set -f
        printf '%s\n' "$(crontab -l; echo $CRONLINE)" | crontab -
        set +f
        echo "s3 sync added to crontab."
    else
        echo "s3 sync already in crontab."
    fi


    ## LOGSEQ ###
    read -p "are you using this bucket to sync logseq? [y/n] " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        printf "\nOK. To avoid a race condition with logseq,\n\twe will sync with s3 before opening logseq by adding the sync to logseq's startup script.\n\tThis will require sudo."
        LOGSEQ_DESKTOP=/var/lib/snapd/desktop/applications/logseq_logseq.desktop
        if [[ ! -f $LOGSEQ_DESKTOP ]]; then
            echo "logseq desktop file not found. I only know how to handle snap packages sorry."
            exit 1
        fi
        sudo cp s3_sync/pre_logseq_sync.sh /usr/local/bin/pre_logseq_sync.sh
        NEW_EXEC='Exec=env BAMF_DESKTOP_FILE_HINT=/var/lib/snapd/desktop/applications/logseq_logseq.desktop  /usr/local/bin/pre_logseq_sync.sh %U'
        ESCAPED_NEW_EXEC=$(printf '%s\n' "$NEW_EXEC" | sed -e 's/[\/&]/\\&/g')

        sudo sed -i "s/^Exec=.*/$ESCAPED_NEW_EXEC/g" $LOGSEQ_DESKTOP
        printf "\nupdated.\n"
    fi
    echo "s3_sync installed."
else
    echo "please define a thing to install"
fi
