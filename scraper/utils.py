import re
import json
import os


def save_products_data(file_name, data):
    data_dir = 'data'
    file_path = os.path.join(data_dir, file_name)

    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)

    with open(file_path, 'w') as f:
        f.write(json.dumps(data))


def remove_html_tags(html_data: str):
    clean = re.compile('<.*?>')  # compile the regular expression pattern to match HTML tags
    return re.sub(clean, '', html_data)  # remove the matched tags from the input string


def find_proper_choice(choices: list, key: str) -> str:
    choice_value = ''

    # choices should be a list of tuples contain database value and human readable text
    for choice_db_value, human_readable_text in choices:
        if (choice_db_value.lower() in key.lower()) or \
                (key.lower() in choice_db_value.lower()) or \
                (key.lower() in human_readable_text.lower()) or \
                (human_readable_text.lower() in key.lower()):

            choice_value = choice_db_value

    return choice_value
