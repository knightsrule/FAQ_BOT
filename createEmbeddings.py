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
import sqlite3
import pickle 

start_url, depth, log_level, secPDFURL, ifSaveHTML = parse_config()
UI_MODE = False

# Parse the URL and get the domain
local_domain = urlparse(start_url).netloc
dbConnection = sqlite3.connect(local_domain + ".db")
cursor = dbConnection.cursor()

def createTable():
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        cursor.execute("CREATE TABLE embeddings (domain TEXT, page TEXT, text TEXT, num_tokens INTEGER, embeddings BLOB)")
        dbConnection.commit()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'")
        table_name = cursor.fetchone()[0]
        print(table_name)

createTable()

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

tokenizer = tiktoken.get_encoding("cl100k_base")
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

# Get all the text files in the text directory
for file in os.listdir("text/" + local_domain + "/"):

    file_info = list(os.path.splitext(file))
    if file_info[1] and file_info[1] == ".txt":

        texts.clear()
        # Open the file and read the text
        with open("text/" + local_domain + "/" + file, "r", encoding="UTF-8") as f:
            text = f.read()
            n_tokens = len(tokenizer.encode(text))
            if n_tokens > max_tokens:
                chunks = split_into_many(text)
                for chunk in chunks:
                    texts.append((chunk, len(tokenizer.encode(chunk))))
            else:                           
                texts.append((text, n_tokens))

        for text_tuple in texts:
            text = text_tuple[0]
            n_tokens = text_tuple[1]
            embedding = openai.Embedding.create(input=text, engine='text-embedding-ada-002')
            embedding_bytes = pickle.dumps(embedding)

            cmd = "INSERT INTO embeddings (domain, page, text, num_tokens, embeddings) VALUES (?, ?, ?, ?, ?)"
            cursor.execute(cmd, (local_domain, file_info[0], text, n_tokens, embedding_bytes))

        dbConnection.commit()

cursor.close()
dbConnection.close()