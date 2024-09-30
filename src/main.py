import sys
import os
import re
import json

import openai

def fill_with_gpt(system_prompt, user_prompt, parameters=None):
    openai.api_key = os.environ['OPENAI_API_KEY']

    ##### Model #####
    if "model" in parameters:
        model = parameters["model"]
    else:
        model = "gpt-4o"
    
    ##### Temperature #####
    if "temperature" in parameters:
        temperature = parameters["temperature"]
    else:
        temperature = 0.0
        
    ##### Frequency Penalty #####
    if "frequency_penalty" in parameters:
        frequency_penalty = parameters["frequency_penalty"]
    else:
        frequency_penalty = 0.0
        
    #### Logit Bias #####
    if "logit_bias" in parameters:
        logit_bias = parameters["logit_bias"]
    else:
        logit_bias = None
    
    ##### Max Tokens #####
    if "max_tokens" in parameters:
        max_tokens = parameters["max_tokens"]
    else:
        max_tokens = 16
        
    ##### Top P #####
    if "top_p" in parameters:
        top_p = parameters["top_p"]
    else:
        top_p = 1.0
    
    ##### Presence Penalty #####
    if "presence_penalty" in parameters:
        presence_penalty = parameters["presence_penalty"]
    else:
        presence_penalty = 0.0

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
        ],
        temperature=temperature,
        frequency_penalty=frequency_penalty,
        logit_bias=logit_bias,
        max_tokens=max_tokens,
        top_p=top_p,
        presence_penalty=presence_penalty
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

def add_link(file_contents, source):
    link = f"""---
Refer to this note for more information: [[{source}]]
"""
    return file_contents + "\n\n" + link


if __name__ == '__main__':
    assert len(sys.argv) == 4, "Usage: python main.py <input_file> <vault_path> <prompt>"
    assert 'OPENAI_API_KEY' in os.environ, 'Please set the OPENAI_API_KEY environment variable.'
    vault_path = sys.argv[1]
    input_file = sys.argv[2]
    prompt = sys.argv[3]

    input_file_path = os.path.join(vault_path, input_file)
    prompt_dir = os.path.abspath(os.path.join("gpts", prompt))
    
    if not os.path.exists(prompt_dir):
        print(f"Prompt {prompt} not found")
        sys.exit(1)
    
    prompt_files = [os.path.join(prompt_dir, path) for path in os.listdir(prompt_dir) if path.endswith(".md") and path != "system.md" and path != "user.md" and path != "title.md"]
    system_prompt_path = os.path.join(prompt_dir, "system.md")
    user_prompt_path = os.path.join(prompt_dir, "user.md")
    title_prompt_path = os.path.join(prompt_dir, "title.md")

    if not os.path.exists(system_prompt_path) or not os.path.exists(user_prompt_path) or not os.path.exists(title_prompt_path):
        print("Prompt files must contain a system prompt, a user prompt, and a title prompt")
        sys.exit(1)

    with open(input_file_path, "r", encoding="utf-8", errors="xmlcharrefreplace") as f:
        input_file_contents = f.read()
        
    # prompt files must contain a user prompt, a system prompt, and a title prompt
    # any other content is optional and can be substituted into the prompts at run time
    
    # The current file can also be substituted into the prompts at run time with [current-file-contents]

    characteristics_path = os.path.join(prompt_dir, "characteristics.json")
    characteristics = json.load(open(characteristics_path))
    title_characteristics = characteristics["title"]
    user_characteristics = characteristics["user"]

    system_prompt = open(system_prompt_path, "r", encoding="utf-8", errors="xmlcharrefreplace").read()
    user_prompt = open(user_prompt_path, "r", encoding="utf-8", errors="xmlcharrefreplace").read()
    title_prompt = open(title_prompt_path, "r", encoding="utf-8", errors="xmlcharrefreplace").read()
    
    system_prompt = re.sub(r"^\s*---[\s\S]*?---", "", system_prompt)
    user_prompt = re.sub(r"^\s*---[\s\S]*?---", "", user_prompt)
    title_prompt = re.sub(r"^\s*---[\s\S]*?---", "", title_prompt)
    input_file_contents = re.sub(r"^\s*---[\s\S]*?---", "", input_file_contents)
    
    system_prompt = system_prompt.replace("[current-file-contents]", input_file_contents)
    user_prompt = user_prompt.replace("[current-file-contents]", input_file_contents)
    title_prompt = title_prompt.replace("[current-file-contents]", input_file_contents)
    
    for prompt_file in prompt_files:
        with open(prompt_file, "r", encoding="utf-8", errors="xmlcharrefreplace") as f:
            prompt_contents = f.read()
            
            basename = os.path.basename(prompt_file).split(".")[0]
            system_prompt = system_prompt.replace(f"[{basename}]", prompt_contents)
            user_prompt = user_prompt.replace(f"[{basename}]", prompt_contents)
            title_prompt = title_prompt.replace(f"[{basename}]", prompt_contents)

    title = fill_with_gpt(system_prompt, title_prompt, parameters=title_characteristics)

    system_prompt = system_prompt.replace("[title]", title)
    user_prompt = user_prompt.replace("[title]", title)
    title_prompt = title_prompt.replace("[title]", title)
    
    print(title_prompt)
    print(f"The title is: {title}")

    # title = re.sub(r"\+", "Plus", title)
    title = re.sub(r"[^a-zA-Z0-9',.: ]", "", title)
    title = re.sub(r"\s+", " ", title)

    if not title.endswith(".md"):
        title_file = title + ".md"
    else:
        title_file = title
        

    response = fill_with_gpt(system_prompt, user_prompt, parameters=user_characteristics)
    print(response.encode(sys.stdout.encoding, errors='replace'))
    response = re.sub(r"^# (.*)", f"# {title}", response)
    response = add_yaml(response, input_file)
    response = add_link(response, input_file)

    response = re.sub(r'[‘’‛]', "'", response)
    response = re.sub(r'[“”‟]', '"', response)

    encoding = "utf-8"

    with open(os.path.join(vault_path, "50-Notes", "51-Notes", title_file), "w", encoding=encoding) as f:
        f.write(response)
    print(f"Created file {os.path.join("50-Notes" "51-Notes", title_file)}")
    print(response)




# See PyCharm help at https://www.jetbrains.com/help/pycharm/
