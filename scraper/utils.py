import re


def remove_html_tags(html_data: str):
    clean = re.compile('<.*?>')  # compile the regular expression pattern to match HTML tags
    return re.sub(clean, '', html_data)  # remove the matched tags from the input string
