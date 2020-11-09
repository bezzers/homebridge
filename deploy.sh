#!/bin/bash

# Set some variables
REGISTRY=submissions.mgti-dal-so-art.mrshmc.com
REPO=$(cat deploy.json | jq -r '.values.image.repo')
TAG=$(cat deploy.json | jq -r '.values.image.tag')
APIURL=https://mgti-dev.api.azu.mrshmc.com/oss2api

# Build the image
IMAGEID=$(docker build -q -t ${REGISTRY}/${REPO}:${TAG} .)
echo $IMAGEID

# Push the image to the submissions repo
docker push ${REGISTRY}/${REPO}:${TAG}

# Register the image for scanning
curl -s \
--request POST \
--url "${APIURL}/register_image" \
--header "X-ApiKey: ${SECOPS_API_KEY}" \
--header "Content-Type: application/json" \
--data-raw "{ \
    \"registry\":\"${REGISTRY}\", \
    \"repo\":\"${REPO}\", \
    \"submitter\":\"paul.beswick@mmc.com\", \
    \"tag\": \"${TAG}\" \
}"

# Loop until the scan has completed
SCAN_COMPLETE=0
until [ ${SCAN_COMPLETE} == 1 ]; do
    sleep 10s
    SCAN_RESULT=$(curl -ks -H "X-ApiKey: ${SECOPS_API_KEY}" ${APIURL}/status?imageHash=${IMAGEID} | jq -r '.image_scan_state')
    if [ ${SCAN_RESULT} == "rejected" ] || [ ${SCAN_RESULT} == "policy_approved" ]; then
        SCAN_COMPLETE=1
    fi
    echo ${SCAN_RESULT}
done

# If the scan was rejected then exit
if [ ${SCAN_RESULT} == "rejected" ]; then
    echo "Scan was rejected"
    exit 1
fi

# Otherwise trigger a deploy
curl \
--request 'POST' \
--url "${APIURL}/update_application" \
--header "X-ApiKey: ${DEPLOY_API_KEY}" \
--header 'Content-Type: application/json' \
--data @deploy.json