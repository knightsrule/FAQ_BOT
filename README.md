# FAQ_BOT

1. Download the git repo to a local directory
2. use a terminal to go to this directory
3. create a python enviornment by executing "python3 -m venv py_env"
4. activate the enviornment by executing "source py_env/bin/activate"
5. Install the requirements by executing "pip -r requirements.txt"
6. Create a copy of config.json and edit this file to include the domain that you want to parse
7. STEP 1: execute crawler by running 'python crawlScrapy.py -c=<new config file>'
8. After this is done, confirm that a new directory "text\<new domain>" was created and contains text files
9. Update enviornment variable to include the openai key. "export OPENAI_API_KEY=<value>"
10. STEP 2: Run "python createEmbeddings.py -c=<new config file>". This will create embeddings.csv and scraped.csv files under "processed"
11. STEP 3: Assuming no errors, run "python answer.py -c=<new config file>"
12. Hit enter on a new line to exit

If needed:
pip install matplotlib 
pip install plotly  
pip install scipy
pip install -U scikit-learn
 