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

    input_file = os.path.join(vault_path, input_file)
    prompt = os.path.join(vault_path, prompt)

    # Read the input file
    with open(input_file, "r") as f:
        input_file_contents = f.read()

    # Read the prompt file
    with open(prompt, "r") as f:
        prompt_contents = f.read()

    system_prompt = re.search(r"```system([\s\S]*?)```", prompt_contents).group(1)
    user_prompt = re.search(r"```user([\s\S]*?)```", prompt_contents).group(1)

    system_prompt = re.sub(r'\[current-file-contents\]', input_file_contents, system_prompt)
    user_prompt = re.sub(r'\[current-file-contents\]', input_file_contents, user_prompt)

    response = fill_with_gpt(system_prompt, user_prompt)
    response = add_yaml(response, input_file)
    title = re.search(r"# (.*)", response).group(1) + ".md"
    with open(os.path.join(vault_path, "500-Zettelkasten", title), "w") as f:
        f.write(response)
    print(f"Created file 500-Zettelkasten/{title}")





# See PyCharm help at https://www.jetbrains.com/help/pycharm/