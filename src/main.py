import sys
import os
import re

import openai


def fill_with_gpt(system_prompt, user_prompt, model="gpt-4-turbo"):
    openai.api_key = os.environ['OPENAI_API_KEY']

    response = openai.chat.completions.create(
        model=model,
        messages=
        [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    )

    return response.choices[0].message.content

def add_yaml(file_contents, source):
    yaml = f"""---
aliases:
tags:
bad_links:
source: {source}
---"""
    return yaml + "\n" + file_contents

if __name__ == '__main__':
    assert len(sys.argv) == 4, "Usage: python main.py <input_file> <vault_path> <prompt>"
    assert 'OPENAI_API_KEY' in os.environ, 'Please set the OPENAI_API_KEY environment variable.'
    vault_path = sys.argv[1]
    input_file = sys.argv[2]
    prompt = sys.argv[3]

    input_file_path = os.path.join(vault_path, input_file)
    prompt = os.path.join(vault_path, prompt)

    # Read the input file
    with open(input_file_path, "r") as f:
        input_file_contents = f.read()

    # Read the prompt file
    with open(prompt, "r") as f:
        prompt_contents = f.read()

    system_prompt = re.search(r"```system([\s\S]*?)```", prompt_contents).group(1)
    user_prompt = re.search(r"```user([\s\S]*?)```", prompt_contents).group(1)
    title_prompt = re.search(r"```title_gpt([\s\S]*?)```", prompt_contents).group(1)



    system_prompt = re.sub(r'\[current-file-contents\]', input_file_contents, system_prompt)
    user_prompt = re.sub(r'\[current-file-contents\]', input_file_contents, user_prompt)
    title_prompt = re.sub(r'\[current-file-contents\]', input_file_contents, title_prompt)

    title = fill_with_gpt(system_prompt, title_prompt)

    system_prompt = re.sub(r'\[title\]', title, system_prompt)
    user_prompt = re.sub(r'\[title\]', title, user_prompt)
    title_prompt = re.sub(r'\[title\]', title, title_prompt)

    if not title.endswith(".md"):
        title_file = title + ".md"
    else:
        title_file = title

    response = fill_with_gpt(system_prompt, user_prompt)
    response = re.sub(r"^# (.*)", f"# {title}", response)
    response = add_yaml(response, input_file)

    if not title.endswith(".md"):
        title += ".md"

    same_file = re.search(r"same_file: (.*)", prompt_contents).group(1)
    assert same_file in ["true", "false"], "same_file must be either true or false"
    if same_file == "true":
        with open(input_file_path, "w") as f:
            f.write(response)
        print(f"Updated file {input_file}")
    else:
        with open(os.path.join(vault_path, "500-Zettelkasten", title), "w") as f:
            f.write(response)
        print(f"Created file {os.path.join("500-Zettelkasten", title)}")





# See PyCharm help at https://www.jetbrains.com/help/pycharm/
