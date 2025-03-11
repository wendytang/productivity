#!/usr/bin/env python3

import json
import csv
import glob
import os
from datetime import datetime
import openai
from typing import Optional, Tuple, List

# Get API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

openai.api_key = OPENAI_API_KEY

def get_ai_analysis(title: str, body: str, labels: List[dict], comments: List[dict]) -> Tuple[str, bool]:
    """Get an AI-generated summary and criticality assessment of the issue."""
    try:
        # Create a string of labels
        label_names = [label['name'] for label in labels]
        labels_str = ', '.join(label_names) if label_names else "No labels"
        
        prompt = f"""Analyze this GitHub issue and provide:
1. A concise summary (max 2 sentences)
2. Whether this issue seems critical (true/false) based on:
   - Impact on users
   - Security implications
   - System stability
   - Data integrity
   - Blocking nature of the issue

Title: {title}
Labels: {labels_str}
Body: {body}

Respond in this format:
Summary: <your_summary>
Critical: <true/false>"""
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.5
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse the response
        summary = ""
        critical = False
        
        for line in result.split('\n'):
            if line.startswith('Summary:'):
                summary = line.replace('Summary:', '').strip()
            elif line.startswith('Critical:'):
                critical_str = line.replace('Critical:', '').strip().lower()
                critical = critical_str == 'true'
        
        return summary, critical
    except Exception as e:
        print(f"Error getting AI analysis: {e}")
        return None, False

def extract_keywords(text):
    # Common technical keywords to look for
    keywords = ['bug', 'feature', 'enhancement', 'ui', 'api', 'error', 'crash', 'performance', 
               'security', 'documentation', 'test', 'cli', 'gui', 'config', 'extension']
    
    # Convert text to lowercase for matching
    text_lower = text.lower()
    
    # Find matching keywords
    found_keywords = [word for word in keywords if word in text_lower]
    
    return found_keywords

def get_involved_people(data):
    """Extract all people involved in the issue."""
    people = set()
    
    # Add author
    if 'author' in data and 'login' in data['author']:
        people.add(data['author']['login'])
    
    # Add assignees
    for assignee in data.get('assignees', []):
        if 'login' in assignee:
            people.add(assignee['login'])
    
    # Add people from comments
    for comment in data.get('comments', []):
        if 'author' in comment and 'login' in comment['author']:
            people.add(comment['author']['login'])
    
    return list(people)

def process_issues():
    # Prepare CSV file
    csv_file = "issue_summary.csv"
    headers = [
        'Issue Number', 
        'Title', 
        'Created Date', 
        'Status', 
        'Assigned', 
        'Number of Responses',
        'People Involved',
        'Critical',
        'AI Summary', 
        'Keywords', 
        'URL'
    ]
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        # Process each JSON file
        for json_file in glob.glob("goose_issue_*.json"):
            print(f"Processing {json_file}...")
            with open(json_file, 'r', encoding='utf-8') as issue_file:
                try:
                    data = json.load(issue_file)
                    
                    # Extract keywords from title, body, and labels
                    keywords = extract_keywords(data['title'] + ' ' + data['body'])
                    keywords.extend([label['name'] for label in data['labels']])
                    keywords = list(set(keywords))  # Remove duplicates
                    
                    # Get AI summary and criticality
                    ai_summary, is_critical = get_ai_analysis(
                        data['title'], 
                        data['body'],
                        data['labels'],
                        data.get('comments', [])
                    )
                    
                    # Get people involved
                    people_involved = get_involved_people(data)
                    
                    # Check if assigned
                    is_assigned = len(data.get('assignees', [])) > 0
                    
                    # Count responses (comments)
                    num_responses = len(data.get('comments', []))
                    
                    # Format created date
                    created_date = datetime.strptime(data['createdAt'], 
                                                   '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')
                    
                    # Create row
                    row = {
                        'Issue Number': data['number'],
                        'Title': data['title'],
                        'Created Date': created_date,
                        'Status': data['state'],
                        'Assigned': 'Yes' if is_assigned else 'No',
                        'Number of Responses': num_responses,
                        'People Involved': ', '.join(people_involved),
                        'Critical': 'Yes' if is_critical else 'No',
                        'AI Summary': ai_summary or "Failed to generate summary",
                        'Keywords': ', '.join(keywords),
                        'URL': data['url']
                    }
                    
                    writer.writerow(row)
                    
                except json.JSONDecodeError as e:
                    print(f"Error processing {json_file}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing {json_file}: {e}")

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("Please set OPENAI_API_KEY environment variable first!")
        exit(1)
    
    process_issues()
    print("\nSummary CSV has been created as 'issue_summary.csv'")