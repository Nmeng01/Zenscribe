import requests
from requests.exceptions import RequestException
import time
import json
import os
from dotenv import load_dotenv
from datetime import date, timedelta
import shutil
import openai

def download(url, idx):
    '''
    Downloads a recording from the specified URL and saves it as an MP3 file.

    Params:
        url (str): The URL of the recording to download.
        idx (int): The index used to generate the filename for the downloaded recording.

    Returns:
        str: The file path of the downloaded recording if successful, otherwise None.

    Raises:
        Exception: If an error occurs during the download process.
    '''
    try:
        recording_response = requests.get(url, auth=(os.getenv('EMAIL'), os.getenv('Z_TOKEN')), stream=True)
        if recording_response.status_code == 200:
            file_path = f'recordings/recording_{idx}.mp3'
            with open(file_path, 'wb') as f:
                for chunk in recording_response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            print(f"Downloaded: {file_path}")
            return file_path
        else:
            print(f"Failed to download {ticket['recording_url']}, status code: {recording_response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading {ticket['recording_url']}: {e}")
        return None

def summarize(file_path, ticket, client, retries, idx):
    '''
    Transcribes a recording and generates a summary of the conversation.

    Params:
        file_path (str): The path to the audio file to be transcribed.
        ticket (dict): A dictionary containing ticket information, including customer and agent details.
        client (openai.OpenAI): An instance of the OpenAI client for making API calls.
        retries (int): The number of retry attempts for the summarization request in case of errors.

    Returns:
        None: The function updates the ticket dictionary with the transcription and summary.

    Raises:
        Exception: If an error occurs during the transcription or summarization process.
    '''
    try:
        txt_fp = f'transcriptions/transcription_{idx}.txt'
        with open(file_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=f
            )
        with open(txt_fp, "w") as t:
            t.write(transcription.text)
        ticket['transcription'] = transcription.text
        messages = [
            {'role': 'system', 'content': 'You are an intelligent assistant.'},
            {'role': 'user', 'content': 
            f'Summarize the issue faced by customer {ticket["customer"]} and how agent {ticket["agent"]} addressed it. ' + 
            f'Indicate if the issue was resolved, using no more than 150 words. Transcript: {transcription.text}'}
        ]
        for attempt in range(retries):
            try:
                chat = client.chat.completions.create(messages=messages, model="gpt-4o")
                print(chat.choices[0].message.content)
                ticket['summary'] = chat.choices[0].message.content
                break  # Exit the retry loop if successful
            except (openai.InternalServerError, RequestException) as e:
                if attempt < retries - 1:
                    wait_time = 3 ** (attempt + 1)  # Exponential backoff
                    print(f"Error: {e}. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Error: {e}. Failed after {retries} attempts.")
        
        return txt_fp
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

# Main code

num_days = 1
curr = num_days
count = 0
tickets_info = []

# Clear the folders before downloading
if os.path.exists('recordings'):
    shutil.rmtree('recordings')
os.makedirs('recordings')

if os.path.exists('transcriptions'):
    shutil.rmtree('transcriptions')
os.makedirs('transcriptions')

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
        'query': f'type:ticket created>{start_time} created<{end_time} via:voice',
        'sort_by': 'created_at'
    }

    # Authenticate and search for tickets within the specified timeframe
    search_response = requests.get(search_url, params=params, auth=(os.getenv('EMAIL'), os.getenv('Z_TOKEN')))
    tickets = []
    while True:
        if search_response.status_code == 200:
            data = search_response.json()
            tickets = data['results']

            for ticket in tickets:
                info = {'id': ticket['id'], 'recording_url': '', 'customer': '', 'agent': '', 'transcription': '', 'summary': ''}
                comments_url = f'https://{subdomain}.zendesk.com/api/v2/tickets/{ticket["id"]}/comments.json'
                comments_response = requests.get(comments_url, auth=(os.getenv('EMAIL'), os.getenv('Z_TOKEN')))

                if comments_response.status_code == 200:
                    comments_data = comments_response.json()
                    # print(json.dumps(comments_data, indent=4))  comment out everything after this loop
                    for comment in comments_data['comments']:
                        recording_url = comment.get('data', {}).get('recording_url')
                        if recording_url:
                            info['recording_url'] = recording_url
                            info['customer'] = comment.get('via', {}).get('source', {}).get('from', {}).get('name')
                            if info['customer'] == 'Brooklyn Low Voltage Supply':
                                info['customer'] = comment.get('via', {}).get('source', {}).get('to', {}).get('name')
                            info['agent'] = comment.get('data', {}).get('answered_by_name')
                            tickets_info.append(info)
                            count += 1

            if data['next_page'] is not None:
                    search_url = data['next_page']
            else:
                break
        else:
            break
    
    curr -= 1

client = openai.OpenAI(api_key=os.getenv("C_TOKEN"))
for idx, ticket in enumerate(tickets_info):
    print(f'Processing file {idx + 1}')
    recording_fp = download(ticket['recording_url'], idx+1)
    if recording_fp:
        transcription_fp = summarize(recording_fp, ticket, client, 3, ticket['id'])
        if transcription_fp:
            attachment_url = f'https://{subdomain}.zendesk.com/api/v2/uploads.json'
            with open(transcription_fp, 'rb') as f:
                response = requests.post(
                    attachment_url, params={'filename': f'transcription_{ticket["id"]}'}, 
                    data=f, headers={'Content-Type': 'text/plain'}, 
                    auth=(os.getenv('EMAIL'), os.getenv('Z_TOKEN'))
                )
            upload_token = response.json()['upload']['token']
            ticket_url = f'https://{subdomain}.zendesk.com/api/v2/tickets/{ticket["id"]}'
            note = {
                'ticket': {
                    'comment': {
                        'body': ticket['summary'], 
                        'public': False, 
                        'uploads': [upload_token]
                    }
                }
            }
            requests.request("PUT", ticket_url, auth=(os.getenv('EMAIL'), os.getenv('Z_TOKEN')), headers={'Content-Type': 'application/json'}, json=note)

    





### Save the support agent's name as well as which call by number
### Next step: Continue testing for cost purposes. 
### Add a check to limit token usage and send alerts if this happens.