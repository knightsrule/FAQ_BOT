import argparse
import json

class ConfigReader():
 
    def __init__(self, *args, **kwargs):
        self.config = {}

    def loadConfig(self):
        # Define the command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument(
        "-config", "-c", required=True, help="config file with base_url, depth and log_level")

        # Parse the command line arguments
        args = parser.parse_args()

        filepath = args.config
        configFile = open(filepath, "r")
        self.config = json.loads(configFile.read())
        configFile.close()

    def readConfigParam(self, param, defaultValue):
        value = self.config.get(param, defaultValue)
        return value
    