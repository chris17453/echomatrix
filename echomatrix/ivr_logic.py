# ivr/ivr_logic.py

from gpt_processor import get_gpt_response

def query_internal_systems(text):
    if "time" in text:
        from datetime import datetime
        return f"The current system time is {datetime.now().strftime('%H:%M:%S')}."
    elif "status of server" in text:
        # Placeholder for real check
        return "All servers are currently operational."
    return None

def handle_input(text):
    # Try internal logic first
    internal_response = query_internal_systems(text)
    if internal_response:
        return internal_response

    # Fallback to GPT
    return get_gpt_response(text)
