# Zenscribe

## Purpose

Customer support agents handle many calls each day, often without breaks between them. This makes it difficult to take detailed notes during or after each call. Capturing every detail of these conversations is crucial, as each could contain a lot of important information.

Zendesk has recently released their own version of this as an additional subscription cost, but at the time of development, there was no such tool and my company had a use for this functionality, so I was asked to create it on my own. 

## Features

This tool is designed to be run daily, summarizing each call made in a 24-hour period. Zenscribe is set up in this repository to be run at 12am ET, summarizing the calls from the previous day. If you would like a more hands on tool to use for individual ticket summaries, please see this web app I created: https://github.com/Nmeng01/Zenscribe-Web-App
1. **Transcription and Summarization:** Utilize OpenAI to transcribe call recordings and generate summaries of each call.
2. **Zendesk Integration:** Save a file of the transcription as well as the summary as an internal comment in the relevant ticket in Zendesk.
3. **Email Summaries:** Send emails to a specified address with a list of the summaries and relevant call details. 

This automation will allow support agents to focus on their conversations with clients without worrying about missing details, enhancing efficiency and service quality. 

## Getting Started Locally

- Clone this repository and store it somewhere you can easily find
- Create an env file following the format of the env.example file in this repository.
- Run 'python3 PATH/TO/FILE/main.py' in your console. The job will take a few minutes depending on how many calls you are analyzing.
- **Note:** Ensure that your Zendesk and OpenAI limits are able to handle the number of requests that you will make to their respective APIs 

