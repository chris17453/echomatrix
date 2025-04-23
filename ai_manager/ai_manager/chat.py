import re
import os
import io
import requests
from datetime import datetime
import openai
import logging

logger = logging.getLogger(__name__)

def chat(prompt_name, data={}, model=None, client=None,prompts=None):
    messages = []
    try:
        if not data:
            data = {}
        logging.info(f"Generating content with data: {data}")

        if not client:
            logger.error("No OpenAI client available")
            return None

        # Validate prompt existence
        if prompt_name not in prompts:
            logging.error(f"Prompt '{prompt_name}' not found in available prompts.")
            return None

        prompt = prompts[prompt_name]
        if prompt is None:
            logging.error(f"Prompt '{prompt_name}' exists but is None.")
            return None

        # Extract placeholders from the prompt
        def extract_placeholders(prompt_text):
            if not prompt_text:  # Handle None or empty string
                return []
            return re.findall(r'{(.*?)}', prompt_text)

        required_keys = set()
        if isinstance(prompt, dict):
            if 'user' in prompt and prompt['user']:
                required_keys.update(extract_placeholders(prompt['user']))
        elif prompt:  # Only process if prompt is not None or empty
            required_keys.update(extract_placeholders(prompt))

        # Check if all required keys are present in the data
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            logging.error(f"Missing required data keys for formatting: {missing_keys}")
            return None

        # Build messages based on prompt structure
        if isinstance(prompt, dict):
            if 'system' in prompt and prompt['system']:
                messages.append({
                    "role": "system",
                    "content": prompt['system']
                })
            if 'user' in prompt and prompt['user']:
                messages.append({
                    "role": "user",
                    "content": prompt['user'].format(**data)
                })
        elif prompt:  # Only process if prompt is not None or empty
            messages.append({
                "role": "user",
                "content": prompt.format(**data)
            })

        # Check if messages is empty
        if not messages:
            logging.error("No messages created from prompt")
            return None

        # Send request to the OpenAI client
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        result = response.choices[0].message.content.strip()
        logging.info("Content generation successful.")
        return result

    except KeyError as key_err:
        logging.error(f"KeyError: Missing data for formatting - {key_err}")
    except Exception as ex:
        logging.error(f"Error during content generation: {ex}")

    return None

