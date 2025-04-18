# echomatrix/gpt_processor.py

import openai
from echomatrix.config import config
from echomatrix.openai import prompt

def get_gpt_response(text):
    answer= prompt("generic",{'text':text})
    return answer

