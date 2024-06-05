import requests
import json
import os
from dotenv import load_dotenv
from datetime import date, timedelta

num_days = 365
curr = num_days
count = 0
while curr > 0:
    load_dotenv()
    yesterday = date.today() - timedelta(days=curr)
    today = date.today() - timedelta(days=curr-1)

    # Specify the timeframe for your search (ISO 8601 format)
    start_time = f'{yesterday}T04:00:00Z'
    end_time = f'{today}T03:59:59Z'
    subdomain = os.getenv('SUBDOMAIN')

    # Search URL
    search_url = f'https://{subdomain}.zendesk.com/api/v2/search.json'
    params = {
        'query': f'type:ticket updated>{start_time} updated<{end_time} via:voice',
        'sort_by': 'updated_at'
    }

    # Authenticate and search for tickets within the specified timeframe
    search_response = requests.get(search_url, params=params, auth=(os.getenv('EMAIL'), os.getenv('TOKEN')))
    tickets = []

    if search_response.status_code == 200:
        data = search_response.json()
        count += len(data['results'])
     
    curr -= 1

print(count/num_days)


    # tickets.extend(data['results'])
    
    # # Check if there is a next page
    # if 'next_page' in data and data['next_page']:
    #     search_response = requests.get(data['next_page'], auth=(os.getenv('EMAIL'), os.getenv('TOKEN')))
    # else:
    #     break



# # Function to download audio attachments from a ticket
# def download_audio_attachments(ticket_id):
#     comments_url = f'https://{subdomain}.zendesk.com/api/v2/tickets/{ticket_id}/comments.json'
#     comments_response = requests.get(comments_url, auth=HTTPBasicAuth(email, api_token))
#     comments = comments_response.json()['comments']
    
#     audio_attachments = []
#     for comment in comments:
#         if 'attachments' in comment:
#             for attachment in comment['attachments']:
#                 if attachment['content_type'].startswith('audio/'):
#                     audio_attachments.append(attachment)
                    
#     for attachment in audio_attachments:
#         audio_url = attachment['content_url']
#         audio_response = requests.get(audio_url, auth=HTTPBasicAuth(email, api_token))
#         file_name = attachment['file_name']
#         with open(file_name, 'wb') as f:
#             f.write(audio_response.content)
#         print(f'Downloaded {file_name}')
    
#     if not audio_attachments:
#         print(f'No audio attachments found in ticket {ticket_id}.')

# # Iterate over each ticket and download audio attachments
# for ticket in tickets:
#     download_audio_attachments(ticket['id'])

# if not tickets:
#     print('No tickets found in the specified timeframe.')
