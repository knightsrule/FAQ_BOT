import openai
from openai.embeddings_utils import distances_from_embeddings
import pandas as pd
import numpy as np
import json
from urllib.parse import urlparse
from config_parser import ConfigReader

config = ConfigReader()
config.loadConfig()
start_url = config.readConfigParam('start_url', '')

# Parse the URL and get the domain
local_domain = urlparse(start_url).netloc


################################################################################
# Step 11
################################################################################

df = pd.read_csv('processed/' + local_domain + '/embeddings.csv', index_col=0)
df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

df.head()

################################################################################
# Step 12
################################################################################


def create_context(
    question, df, max_len=1800, size="ada"
):
    """
    Create a context for a question by finding the most similar context from the dataframe
    """

    # Get the embeddings for the question
    q_embeddings = openai.Embedding.create(
        input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # Get the distances from the embeddings
    df['distances'] = distances_from_embeddings(
        q_embeddings, df['embeddings'].values, distance_metric='cosine')

    returns = []
    cur_len = 0

    # Sort by distance and add the text to the context until the context is too long
    for i, row in df.sort_values('distances', ascending=True).iterrows():

        # Add the length of the text to the current length
        cur_len += row['n_tokens'] + 4

        # If the context is too long, break
        if cur_len > max_len:
            break

        # Else add it to the text that is being returned
        returns.append(row["text"])

    # Return the context
    return "\n\n###\n\n".join(returns)


def answer_question(
    df,
    # model="text-davinci-003",
    model="gpt-3.5-turbo",
    question="Am I allowed to publish model outputs to Twitter, without a human review?",
    max_len=1800,
    size="ada",
    debug=False,
    max_tokens=150,
    stop_sequence=None
):
    """
    Answer a question based on the most similar context from the dataframe texts
    """
    context = create_context(
        question,
        df,
        max_len=max_len,
        size=size,
    )
    # If debug, print the raw model response
    if debug:
        print("Context:\n" + context)
        print("\n\n")

    try:
        # Create a completions using the questin and context
        response = openai.ChatCompletion.create(
            messages=[
                {"role": "system", "content": f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}"},
                {"role": "user", "content": f"Question: {question}"},
            ],
            # messages=[
            #    {"role": "system", "content": "Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\n"},
            #    {"role": "user", "content": f"Context: {context}\n\n---\n\nQuestion: {question}"},
            # ],
            temperature=0.2,
            max_tokens=max_tokens,
            top_p=0.8,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )

        message = response["choices"][0]["message"]
        if message:
            # print(message["role"] + ": " + message["content"])
            # print(choice)
            # return response["choices"][0]["text"].strip()
            return message
        else:
            return ""
    except Exception as e:
        print(e)
        return ""

################################################################################
# Step 13
################################################################################


text = input("Ask me a question: ")
while text:
    print(answer_question(df, question=text, debug=True))
    text = input("Ask me a question: ")
