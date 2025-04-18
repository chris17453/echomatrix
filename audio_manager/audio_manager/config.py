default_config={
                'audio_manager': {
                    'db_path': '',
                    'locations': {
                        'local': {
                            'type': 'local',
                            'path': '/opt/audio/'
                        },
                        's3_a': {
                            'type': 's3',
                            'bucket': '',
                            'path': ''
                        }
                    },
                    'ai': {
                        'id': 1
                    },
                    'user': {
                        'id': None
                    },
                    'openai': {
                        'api_key': '',
                        'orginization_id': '',
                        'whisper_model': "whisper-1",
                        'gpt_model': "gpt-4-turbo",
                        'tts_voice': "alloy",
                        'tts_model': "tts-1"
                    }
                }
            }