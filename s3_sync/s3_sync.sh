#!/bin/bash
set -e
SETTINGS_PATH=${HOME}/.productivity_porn_settings
export $(cat ${SETTINGS_PATH} | xargs) 1> /dev/null
export $(cat ${PERSONAL_SECRETS_PATH} | xargs) 1> /dev/null
MINUTES_AGO=$(date +%Y-%m-%dT%H:%M:00 --date "-$S3_SYNC_LAG_MINUTES min")

UPDATED_FILES=$(find $S3_SYNC_PATH -type f -newermt $MINUTES_AGO)
if [ -z "$UPDATED_FILES" ]; then
	echo "No files changed in the last ${S3_SYNC_LAG_MINUTES} in ${S3_SYNC_PATH} to write to AWS, skipping upload."
else
	echo "writing new files to AWS..."
	docker run --rm \
	-e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
	-e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
	-v ${S3_SYNC_PATH}:/aws amazon/aws-cli s3 sync . s3://${S3_BUCKET_NAME}
	echo "new files written to AWS."
fi
echo "pulling files from AWS..."
	docker run --rm \
	-e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
	-e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
	-v ${S3_SYNC_PATH}:/aws amazon/aws-cli s3 sync s3://${S3_BUCKET_NAME} .
	echo "new files pulled from AWS."

if [ "$EUID" -ne 0 ]; then
	pkexec chown -R  $S3_SYNC_CHOWN_USER_GROUP $S3_SYNC_PATH
else
	chown -R  $S3_SYNC_CHOWN_USER_GROUP $S3_SYNC_PATH
fi