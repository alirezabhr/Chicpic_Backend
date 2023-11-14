import json
import os
import re
import logging

def log_function_call(func):

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logging.error(f"Error in function {func.__name__} with args {args} and kwargs {kwargs}")
            raise e

    return wrapper

def log_function_call2(func):
    logger = logging.getLogger(func.__name__)

    def wrapper(*args, **kwargs):
        logger.info(f"Start function {func.__name__} with args {args} and kwargs {kwargs}")
        result = func(*args, **kwargs)
        return result

    return wrapper


def remove_html_tags(html_data: str):
    clean = re.compile('<.*?>')  # compile the regular expression pattern to match HTML tags
    return re.sub(clean, '', html_data)  # remove the matched tags from the input string


def find_proper_choice(choices: list, key: str) -> str:
    # Choices should be a list of tuples contain database value and human-readable text
    for choice_db_value, human_readable_text in choices:
        if choice_db_value.lower() == key.lower() or human_readable_text.lower() == key.lower():
            return choice_db_value

    raise Exception(f'Choice not found. choices: {choices}, key: {key}')


def save_data_file(file_relative_path: str, data: list):
    # Get absolute address of this package
    package_dir = os.path.dirname(os.path.abspath(__file__))

    # Get absolute address of file
    file_path = os.path.join(package_dir, file_relative_path)

    # Make directory if it does not exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save data in file
    with open(file_path, 'w') as f:
        f.write(json.dumps(data))


def read_data_json_file(file_path: str):
    # Get absolute address of this package
    package_dir = os.path.dirname(os.path.abspath(__file__))

    # Get absolute address of file
    file_path = os.path.join(package_dir, file_path)

    # Read data from file
    with open(file_path, 'r') as f:
        data = json.loads(f.read())

    return data
