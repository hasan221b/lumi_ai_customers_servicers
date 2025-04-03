import os
import yaml
from dotenv import load_dotenv

load_dotenv()

# Path to config.yml, relative to config.py
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config", "config.yml")

class Config:
    def __init__(self, config_path=CONFIG_PATH):
        # Load the configuration file
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
         # Calculate the project root (parent of the config/ directory)
        self.PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(config_path), ".."))
        # Helper function to convert relative paths to absolute paths
        def to_absolute_path(relative_path):
            # Replace backslashes with forward slashes for Linux compatibility
            normalized_path = relative_path.replace('\\', '/')
            # Join with project root
            return os.path.join(self.PROJECT_ROOT, normalized_path)
        # Set absolute paths for file-based configurations
        self.DATA_PATH = to_absolute_path(config_data['faqs_path'])
        # Add other paths if they exist in your config.yml
        if 'index_path' in config_data:
            self.INDEX_PATH = to_absolute_path(config_data['index_path'])
        if 'logging' in config_data:
            self.PIPELINE_LOGGER = to_absolute_path(config_data['logging']['pipeline_log_file'])
            self.APP_LOGGER = to_absolute_path(config_data['logging']['app_log_file'])
        
        # Other non-file configurations (example)
        self.EMBEDDING_MODEL = config_data['embedding_model']
        self.LLM_MODEL = config_data['llm_model']
        self.SENTIMENT_MODEL = config_data['sentiment_model']
        self.ZERO_SHOT_MODEL = config_data['zero_shot_model']
        self.TEMBERATURE =config_data['temperature']
        self.DATA_PATH = config_data['faqs_path']
        self.INDEX_PATH = config_data['index_path']
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.LOGGER_FORMAT = config_data['logging']['format']
        self.PIPELINE_LOGGER = config_data['logging']['pipeline_log_file']
        self.APP_LOGGER = config_data['logging']['app_log_file']
# Instantiate the config object
config = Config()
