# python -m flask --app apig run

from flask import Flask, jsonify, request
import openai
from openai.embeddings_utils import distances_from_embeddings
import pandas as pd
import numpy as np
import json
from urllib.parse import urlparse

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # initialize the CORS extension

start_url = 'https://www.mower.com'
start_url = 'https://www.televox.com'
start_url = 'https://www.mhs.net'

# Parse the URL and get the domain
local_domain = urlparse(start_url).netloc

df = {}

# define a function to perform initialization tasks


def init_app():
    global df
    print('len of df', len(df))
    print("Initializing app...")

    # perform one-time setup tasks here, such as loading configuration settings

    ################################################################################
    # Step 11
    ################################################################################

    df = pd.read_csv('processed/' + local_domain +
                     '/embeddings.csv', index_col=0)
    df['embeddings'] = df['embeddings'].apply(eval).apply(np.array)

    df.head()


# use the before_first_request decorator to call the init_app function
@app.before_first_request
def before_first_request():
    init_app()


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
    model="text-davinci-003",
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
        response = openai.Completion.create(
            prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say \"I don't know\"\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
            temperature=0,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )
        return response["choices"][0]["text"].strip()
    except Exception as e:
        print(e)
        return ""


@app.route('/query', methods=['POST'])
def doQuery():
    global df
    print('len of df', len(df))

    print('in doQuery')
    if request.method == 'POST':
        print('in post')

        print('requset is: ', request)
        # read the message body
        message_body = request.get_json()

        print('message body is: ', message_body)
        # read the query from body
        query = message_body["query"]
        print('query is: ', query)

        response = answer_question(df, question=query, debug=False)

        # return a response
        return response
    else:
        print("Invalid method")
