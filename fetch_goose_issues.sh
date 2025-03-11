#!/bin/bash

# Get today's date for folder name
TODAY=$(date +%Y-%m-%d)

# Create directory if it doesn't exist
mkdir -p ~/Development/productivity/$TODAY
cd ~/Development/productivity/$TODAY

# Get all issue numbers from the last 48 hours and process each one
gh issue list -R block/goose -S "created:>$(date -v-48H +%Y-%m-%d)" --json number | jq -r '.[].number' | while read issue; do
    gh issue view $issue -R block/goose --comments --json author,body,comments,createdAt,labels,number,state,title,url > "goose_issue_${issue}.json"
done

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY environment variable is not set"
    exit 1
fi


# Run the Python script to summarize issues
uv run python summarize_issues.py

