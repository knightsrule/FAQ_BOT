import argparse
import json


def parse_config():
    # Define the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-config", "-c", required=True, help="config file with base_url, depth and log_level")

    # Parse the command line arguments
    args = parser.parse_args()

    configFilePath = args.config
    configFile = open(configFilePath, "r")
    config = json.loads(configFile.read())
    configFile.close()

    # Define root domain to crawl
    start_url = config["start_url"]
    depth = config.get("depth", 3)
    log_level = config.get('log_level', "DEBUG")
    secPDFURL = config.get("secPDFURL", "")
    return start_url, depth, log_level, secPDFURL
