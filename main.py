import requests
from requests.exceptions import RequestException
import time
import os
from dotenv import load_dotenv
from datetime import date, timedelta
import shutil
import openai
import asyncio
from mutagen.mp3 import MP3
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import SendMailPostRequestBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
import logging
import traceback


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
        recording_response = requests.get(url, auth=(os.getenv('Z_EMAIL'), os.getenv('Z_TOKEN')), stream=True)
        if recording_response.status_code == 200:
            file_path = f'recordings/recording_{idx}.mp3'
            with open(file_path, 'wb') as f:
                for chunk in recording_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded: {file_path}")
            return file_path
        else:
            logging.error(f"Failed to retrieve call recording for ticket {idx}: %s", traceback.format_exc())
            return None
    except Exception as e:
        logging.error(f"An issue with the recording file occurred with ticket {idx}: %s", traceback.format_exc())
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
        messages_summary = [
            {'role': 'system', 'content': 'You are an intelligent assistant.'},
            {'role': 'user', 'content': 
            f'Summarize the issue faced by customer {ticket["customer"]} and how agent {ticket["agent"]} addressed it. Include the name of the customer\'s company if mentioned.' + 
            f'Then, if the issue was resolved, say "This issue was resolved.", otherwise say "This issue was not resolved." ' +
            f'Use no more than 150 words. Transcript: {transcription.text}'}
        ]
        for attempt in range(retries):
            try:
                chat = client.chat.completions.create(messages=messages_summary, model="gpt-4o")
                print(chat.choices[0].message.content)
                ticket['summary'] = chat.choices[0].message.content
                messages_company = [
                    {'role': 'system', 'content': 'You are an intelligent assistant.'},
                    {'role': 'user', 'content': f'Return only the name of customer {ticket["customer"]}\'s company or Unknown based on this summary: {ticket["summary"]}.'}
                ]
                chat = client.chat.completions.create(messages=messages_company, model="gpt-4o")
                ticket['company'] = chat.choices[0].message.content
                if "This issue was resolved" in ticket['summary']:
                    ticket['resolved'] = True
                break  
            except (openai.InternalServerError, RequestException) as e:
                if attempt < retries - 1:
                    wait_time = 3 ** (attempt + 1)
                    time.sleep(wait_time)
                else:
                    print(f"Error: {e}. Failed after {retries} attempts.")
                    logging.error(f"An error with OpenAI occurred while processing ticket {idx}")
        
        return txt_fp
    except Exception as e:
        logging.error(f"Could not process transcription for ticket {idx}.")
        return None

# Main code

tickets_info = []

logging.basicConfig(
    filename='error_log.txt',  
    filemode='a',              
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR
)
# Clear the folders before downloading
if os.path.exists('recordings'):
    shutil.rmtree('recordings')
os.makedirs('recordings')

if os.path.exists('transcriptions'):
    shutil.rmtree('transcriptions')
os.makedirs('transcriptions')

load_dotenv()
yesterday = date.today() - timedelta(days=1)
today = date.today()
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
search_response = requests.get(search_url, params=params, auth=(os.getenv('Z_EMAIL'), os.getenv('Z_TOKEN')))
tickets = []
while True:
    if search_response.status_code == 200:
        data = search_response.json()
        tickets = data['results']
        for ticket in tickets:
            info = {'id': ticket['id'], 'recording_url': '', 'customer': '', 'agent': '', 'transcription': '', 'summary': '', 'resolved': False, 'duration': (), 'company': ''}
            comments_url = f'https://{subdomain}.zendesk.com/api/v2/tickets/{ticket["id"]}/comments.json'
            comments_response = requests.get(comments_url, auth=(os.getenv('Z_EMAIL'), os.getenv('Z_TOKEN')))
            if comments_response.status_code == 200:
                comments_data = comments_response.json()
                for comment in comments_data['comments']:
                    recording_url = comment.get('data', {}).get('recording_url')
                    if recording_url:
                        info['recording_url'] = recording_url
                        info['customer'] = comment.get('via', {}).get('source', {}).get('from', {}).get('name')
                        if info['customer'] == 'Brooklyn Low Voltage Supply':
                            info['customer'] = comment.get('via', {}).get('source', {}).get('to', {}).get('name')
                        info['agent'] = comment.get('data', {}).get('answered_by_name')
                        tickets_info.append(info)
        if data['next_page'] is not None:
                search_url = data['next_page']
        else:
            break
    else:
        break


client = openai.OpenAI(api_key=os.getenv("C_TOKEN"))
for idx, ticket in enumerate(tickets_info):
    print(f'Processing file {idx + 1}')
    recording_fp = download(ticket['recording_url'], idx+1)
    try:
        audio = MP3(recording_fp)
    except Exception:
        logging.error(f"An error occurred with ticket {idx}: %s", traceback.format_exc())
        continue
    ticket['duration'] = (int(audio.info.length//60), int(audio.info.length%60))
    if recording_fp:
        transcription_fp = summarize(recording_fp, ticket, client, 3, ticket['id'])
        if transcription_fp:
            attachment_url = f'https://{subdomain}.zendesk.com/api/v2/uploads.json'
            with open(transcription_fp, 'rb') as f:
                response = requests.post(
                    attachment_url, params={'filename': f'transcription_{ticket["id"]}'}, 
                    data=f, headers={'Content-Type': 'text/plain'}, 
                    auth=(os.getenv('Z_EMAIL'), os.getenv('Z_TOKEN'))
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
            if ticket['summary']:
                requests.request("PUT", ticket_url, auth=(os.getenv('Z_EMAIL'), os.getenv('Z_TOKEN')), headers={'Content-Type': 'application/json'}, json=note)

# Send email
sorted_tickets = sorted(tickets_info, key=lambda x: x['resolved'])
credentials = credentials = ClientSecretCredential(
    tenant_id=os.getenv("TENANT_ID"),
    client_id=os.getenv("EMAIL_ID"),
    client_secret=os.getenv("EMAIL_SECRET"),
)
scopes = ["https://graph.microsoft.com/.default"]
graph_client = GraphServiceClient(credentials, scopes)
email = "<br><br>".join(
    [f"<b>Ticket {ticket['id']}: {'Resolved' if ticket['resolved'] else 'Not Resolved'} | Length of call: {ticket['duration'][0]} minutes {ticket['duration'][1]} seconds | Company: {ticket['company']}</b><br>{ticket['summary']}" for ticket in sorted_tickets]
)

async def send_email():
    request_body = SendMailPostRequestBody(
        message=Message(
            subject="Ticket Summaries " + yesterday.strftime('%m/%d/%Y'),
            body=ItemBody(
                content_type=BodyType.Html,
                content=email
            ),
            to_recipients=[
                Recipient(
                    email_address=EmailAddress(
                        address=os.getenv("R_EMAIL")
                    )
                )
            ],
            # cc_recipients=[
            #     Recipient(
            #         email_address=EmailAddress(
            #             address="danas@contoso.com"
            #         )
            #     )
            # ]
        ),
        save_to_sent_items=False
    )

    await graph_client.users.by_user_id(os.getenv("S_EMAIL")).send_mail.post(request_body)

asyncio.run(send_email())
