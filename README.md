# Zenscribe

## Purpose

Customer support agents handle many calls each day, often without breaks between them. This makes it difficult to take detailed notes during or after each call, which is an issue because agents returning to this ticket at a later time/date need to be able to get up to speed on a customer's issue quickly. We can solve this problem by using Zenscribe, a script set up to automatically transcribe and summarize voice calls saved to Zendesk at the end of each day.  

Zendesk has recently released their own version of this as part of their Advanced AI add-on subscription.

## Features

1. **Transcription and Summarization:** Utilize OpenAI to transcribe call recordings and generate summaries of each call.
2. **Zendesk Integration:** Save a file of the transcription as well as the summary as an internal comment in the relevant ticket in Zendesk.
3. **Email Summaries:** Send emails to a specified address with a list of the summaries and relevant call details.

This tool is designed to be run daily, summarizing each call made in a 24-hour period. Zenscribe is set up in this repository to be run at 12am ET, summarizing the calls from the previous day. If you would like a more hands on tool to use for individual ticket summaries, please see the repository of a [web app](https://github.com/Nmeng01/Zenscribe-Web-App) I created.


