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

    CRONLINE="*/${S3_SYNC_LAG_MINUTES} * * * * /bin/bash /usr/local/bin/s3_sync.sh"
    printf "attempting to add ${CRONLINE} to crontab..."
    if [[ $(crontab -l | egrep -v "^(#|$)" | grep -q '/bin/bash /usr/local/bin/s3_sync.sh'; echo $?) == 1 ]]; then
        echo "s3 sync not in crontab. adding..."
        set -f
        printf '%s\n' "$(crontab -l; echo $CRONLINE)" | crontab -
        set +f
        echo "s3 sync added to crontab."
    else
        echo "s3 sync already in crontab."
    fi
    echo "s3 sync install completed."
else
    echo "please define a thing to install"
fi
