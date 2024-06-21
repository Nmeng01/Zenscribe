# Zenscribe

## Purpose

Our technology customer support agents handle many calls each day, often without breaks between them. This makes it difficult to take detailed notes during or after each call. Capturing every detail of these conversations is crucial, as they can contain a wealth of important information.

Currently, Zendesk saves all call recordings, but reviewing these recordings manually is impractical, especially when they can be over half an hour long. To address this, we aim to automate the note-taking process using OpenAI's API for text summarization and Zendesk's APIs.

## Key Features

1. **Automated Summarization:** Use OpenAI's API to convert call recordings into text summaries.
2. **Zendesk Integration:** Automatically associate these summaries with the relevant tickets in Zendesk.
3. **Scheduled Execution:** Run the script daily to summarize calls from the last workday, ensuring timely and accurate records.

This automation will allow support agents to focus on their conversations with clients without worrying about missing details, enhancing efficiency and service quality.

## Getting Started (locally)

- Place your Zendesk subdomain, email, and token, as well as your OpenAI token in an env file (as shown in the env.example)
- You are free to change the ChatGPT prompt in the summarize() function to better suit your needs
- Ensuring that you are in the root directory, run 'python3 main.py' in your console. The job will take a few minutes depending on how many calls you are analyzing.
- **Note:** Ensure that your Zendesk and OpenAI limits are able to handle the number of requests that you will make to their respective APIs 

## Next steps
The future of this idea is quite exciting, as it makes our data more readily available for analysis. If we could gather data from even the last year, we would have an immense trove of information that could be queried and organized in a database. As most people are aware, once the data is saved and available, the possibilities are endless: from training our own LLM model to producing guides on commonly asked questions, the power of data is quite remarkable in today's world of technology, and to a business, it could mean cutting costs immensely. We are very happy with what we have produced so far, but this is only step one to a multitude of opportunities.
