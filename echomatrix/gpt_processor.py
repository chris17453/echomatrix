# echomatrix/gpt_processor.py

import openai
from echomatrix import config

openai.api_key = config.openai_api_key

def get_gpt_response(text):
    response = openai.ChatCompletion.create(
        model=config.gpt_model,
        messages=[
            {"role": "system", "content": "You are an IVR assistant."},
            {"role": "user", "content": text}
        ]
    )
    return response["choices"][0]["message"]["content"]
