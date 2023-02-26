################################################################################
# Step 5
################################################################################


import os
import pandas as pd
import tiktoken
import openai
from openai.embeddings_utils import distances_from_embeddings
import numpy as np
import json
from urllib.parse import urlparse
from config_parser import parse_config

start_url, depth, log_level = parse_config()

# Parse the URL and get the domain
local_domain = urlparse(start_url).netloc


def remove_newlines(serie):
    serie = serie.str.replace('\n', ' ')
    serie = serie.str.replace('\\n', ' ')
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('  ', ' ')
    return serie


################################################################################
# Step 6
################################################################################

# Create a list to store the text files
texts = []

# Create a directory to store the csv files
if not os.path.exists("processed"):
    os.mkdir("processed")

if not os.path.exists("processed/"+local_domain+"/"):
    os.mkdir("processed/" + local_domain + "/")


# Get all the text files in the text directory
for file in os.listdir("text/" + local_domain + "/"):

    # Open the file and read the text
    with open("text/" + local_domain + "/" + file, "r", encoding="UTF-8") as f:
        text = f.read()
        # print(file, '\n', file[11:-4]
        #      .replace('-', ' ')
        #      .replace('_', ' ')
        #      .replace('#update', ''), '\n\n')

        # Omit the first 11 lines and the last 4 lines, then replace -, _, and #update with spaces.
        texts.append((file, text))

# Create a dataframe from the list of texts
df = pd.DataFrame(texts, columns=['fname', 'text'])

# Set the text column to be the raw text with the newlines removed
df['text'] = df.fname + ". " + remove_newlines(df.text)
df.to_csv('processed/' + local_domain + '/scraped.csv')
df.head()

################################################################################
# Step 7
################################################################################

# Load the cl100k_base tokenizer which is designed to work with the ada-002 model
tokenizer = tiktoken.get_encoding("cl100k_base")

df = pd.read_csv('processed/' + local_domain + '/scraped.csv', index_col=0)
df.columns = ['title', 'text']

# Tokenize the text and save the number of tokens to a new column
df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))

# Visualize the distribution of the number of tokens per row using a histogram
df.n_tokens.hist()

################################################################################
# Step 8
################################################################################

max_tokens = 500

# Function to split the text into chunks of a maximum number of tokens


def split_into_many(text, max_tokens=max_tokens):

    # Split the text into sentences
    sentences = text.split('. ')

    # Get the number of tokens for each sentence
    n_tokens = [len(tokenizer.encode(" " + sentence))
                for sentence in sentences]

    chunks = []
    tokens_so_far = 0
    chunk = []

    # Loop through the sentences and tokens joined together in a tuple
    for sentence, token in zip(sentences, n_tokens):

        # If the number of tokens so far plus the number of tokens in the current sentence is greater
        # than the max number of tokens, then add the chunk to the list of chunks and reset
        # the chunk and tokens so far
        if tokens_so_far + token > max_tokens:
            chunks.append(". ".join(chunk) + ".")
            chunk = []
            tokens_so_far = 0

        # If the number of tokens in the current sentence is greater than the max number of
        # tokens, go to the next sentence
        if token > max_tokens:
            continue

        # Otherwise, add the sentence to the chunk and add the number of tokens to the total
        chunk.append(sentence)
        tokens_so_far += token + 1

    return chunks


shortened = []

# Loop through the dataframe
for row in df.iterrows():

    # If the text is None, go to the next row
    if row[1]['text'] is None:
        continue

    # If the number of tokens is greater than the max number of tokens, split the text into chunks
    if row[1]['n_tokens'] > max_tokens:
        shortened += split_into_many(row[1]['text'])

    # Otherwise, add the text to the list of shortened texts
    else:
        shortened.append(row[1]['text'])

################################################################################
# Step 9
################################################################################

df = pd.DataFrame(shortened, columns=['text'])
df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))
df.n_tokens.hist()

################################################################################
# Step 10
################################################################################

df['embeddings'] = df.text.apply(lambda x: openai.Embedding.create(
    input=x, engine='text-embedding-ada-002')['data'][0]['embedding'])
df.to_csv('processed/' + local_domain + '/embeddings.csv')
df.head()
