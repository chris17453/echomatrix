import os
import re
from typing import Dict, Any

from echomatrix.config import client, config, logger


def get_prompts() -> Dict[str, Any]:
    """
    Load prompts from configured directory with error handling.
    
    Returns:
        Dict[str, Any]: Dictionary mapping prompt names to their content
    """
    directory_path = config.folders.prompts;
    prompts = {}
    
    if not directory_path or not os.path.isdir(directory_path):
        logger.error(f"Prompts directory not found: {directory_path}")
        return prompts
    
    try:
        for filename in os.listdir(directory_path):
            if not filename.endswith('.txt'):
                continue
                
            basename = filename.split('.')[0]
            file_path = os.path.join(directory_path, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    if '.system.txt' in filename:
                        if basename not in prompts:
                            prompts[basename] = {}
                        prompts[basename]['system'] = file.read()
                    elif '.user.txt' in filename:
                        if basename not in prompts:
                            prompts[basename] = {}
                        prompts[basename]['user'] = file.read()
                    else:
                        prompts[basename] = file.read()
                logger.debug(f"Loaded prompt: {basename} from {filename}")
            except (IOError, OSError) as e:
                logger.error(f"Failed to read prompt file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error accessing prompts directory {directory_path}: {e}")
    
    return prompts

def prompt(prompt_name, data={}):
    messages = []
    print (prompt_name)
    try:
        logger.info(f"Generating content with data: {data}")

        # Validate prompt existence
        if prompt_name not in prompts:
            logger.error(f"Prompt '{prompt_name}' not found in available prompts.")
            return None

        prompt = prompts[prompt_name]

        # Extract placeholders from the prompt
        def extract_placeholders(prompt_text):
            return re.findall(r'{(.*?)}', prompt_text)

        required_keys = set()
        if isinstance(prompt, dict):
            if 'user' in prompt:
                required_keys.update(extract_placeholders(prompt['user']))
        else:
            required_keys.update(extract_placeholders(prompt))

        # Check if all required keys are present in the data
        missing_keys = required_keys - set(data.keys())
        if missing_keys:
            logger.error(f"Missing required data keys for formatting: {missing_keys}")
            return None

        # Build messages based on prompt structure
        if isinstance(prompt, dict):
            if 'system' in prompt:
                messages.append({
                    "role": "system",
                    "content": prompt['system']
                })
            if 'user' in prompt:
                messages.append({
                    "role": "user",
                    "content": prompt['user'].format(**data)
                })
        else:
            messages.append({
                "role": "user",
                "content": prompt.format(**data)
            })

        # Send request to the OpenAI client
        response = client.chat.completions.create(
            model=config.openai.gpt_model,
            messages=messages
        )

        result = response.choices[0].message.content.strip()
        logger.info("Content generation successful.")
        return result

    except KeyError as key_err:
        logger.error(f"KeyError: Missing data for formatting - {key_err}")
    except Exception as ex:
        logger.error(f"Error during content generation: {ex}")

    return None


# Load prompts once at module load time
try:
    prompts = get_prompts()
    logger.info(f"Loaded {len(prompts)} prompt templates")
except Exception as e:
    logger.critical(f"Failed to load prompts: {e}")
    prompts = {}


prompts=get_prompts()