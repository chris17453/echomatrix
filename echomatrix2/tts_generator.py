
def generate_speech(text, model=None):
    """
    Generate speech from text and save it in the audio directory structure
    
    Args:
        text (str): The text to convert to speech
        model (str, optional): The TTS model/voice to use (defaults to config)
    
    Returns:
        str: Path to the generated WAV file for Asterisk
    """
    # Use configured model if none provided
    if not model:
        model = config.openai.tts_voice
    
    # Call OpenAI API to generate speech
    try:
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {config.openai.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",  # OpenAI's TTS model
            "input": text,
            "voice": model
        }
        
        logger.info(f"Generating TTS for: '{text[:50]}...' using voice: {model}")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"TTS API error: {response.status_code}, {response.text}")
            return None
        
        # Save MP3 file
        with open(mp3_path, "wb") as f:
            f.write(response.content)
        
        
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return None


