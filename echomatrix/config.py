default_config={
    "sip_manager": {
        "log_level" :  5,
        "public_ip" :  None ,
        "public_port" :  5060 ,
        "domain" :  None,
        "username" :  None,
        "password" :  None,
        "outbound_proxy" : None,
        "contact" :  None,
        "no_vad" :  True ,
        "enable_ice" :  True ,
        "ec_tail_len" :  0 ,
        "tx_drop_pct" :  0 ,
        "clock_rate" :  8000 ,
        "snd_clock_rate" :  8000 ,
        "nat_type_in_sdp" :  4 ,
        "quality" :  10 ,
        "ptime" :  20 ,
        "channel_count" :  1 ,
        "ec_options" :  0 ,
        "silence_check_interval" :  100 ,
        "stun_server" :  "stun.l.google.com:19302" ,
        "nat_keep_alive_interval" :  30 ,
        "bound_address" :  "0.0.0.0" ,
        "pcmu_codec" :  "PCMU/8000" ,
        "pcma_codec" :  "PCMA/8000" ,
        "pcmu_priority" :  255 ,
        "pcma_priority" :  254 ,
        "sample_rate" :  8000 ,
        "sample_width" :  2 ,
        "register" :  False ,
        "welcome_delay" :  100 , # Delay in ms before playing welcome message ,
        "welcome_message_length" :  3000,  # Delay in ms before starting ,
        "silence_duration" :  1000,  # How long it needs to be silent in ms before an event triggers ,
        "silence_threshold" :  100,  # What the silence level is ,
        "silence_check_interval" :  50,  # How often to check for silence ,
        "max_call_length" :  240,  # How long before we forcibly disconnect ,
        "audio_format" :  "wav",  # Should always be pcm, wav is an option but not worked out ,
        "auto_answer" :  True,  # Pickup all incoming calls ,
        "welcome_message" :  None,
        "disconnect_message" :  None,
        "recording_dir" :  "recordings" 
    }
}


config={}
engine_instance={}