import os
import time
import wave
import logging
import pjsua2 as pj
import numpy as np

logger = logging.getLogger(__name__)
audio_recorders = {}

class AudioRecorder:
    @staticmethod
    def start_recording(call, output_path, config):


        try:
            call_info = call.getInfo()
            call_id = call_info.callIdString
            logger.info(f"Setting up recording for call {call_id}")
            recorder = pj.AudioMediaRecorder()
            recorder.output_path            = output_path
            recorder.last_size              = 0
            recorder.last_check_time        = time.time()
            recorder.silence_threshold      = config.silence_threshold
            recorder.silence_duration       = config.silence_duration
            recorder.silence_check_interval = config.silence_check_interval
            recorder.sample_rate            = config.sample_rate
            recorder.sample_width           = config.sample_width
            recorder.silence_detected       = False
            recorder.call_ref               = call
            recorder.history_length         = 10
            recorder.volume_history         = []
            recorder.speech_segments        = []
            
            recorder.recording_start_time    = time.time()
            recorder.recording_start_time_ms = int(recorder.recording_start_time * 1000)
            recorder.silence_start_time_ms   = None
            recorder.current_speech_start_ms = 0
            recorder.recording_start_time_ms = 0


            recorder.createRecorder(output_path)

            for media in call_info.media:
                if media.type == pj.PJMEDIA_TYPE_AUDIO and media.status == pj.PJSUA_CALL_MEDIA_ACTIVE:
                    try:
                        audio_media = call.getAudioMedia(media.index)
                        recorder.audio_media = audio_media
                        audio_media.startTransmit(recorder)
                        logger.info("Connected audio to recorder")
                        break
                    except Exception as e:
                        logger.error(f"Error getting audio media: {e}")


            audio_recorders[call_id] = recorder
            return recorder
        except Exception as e:
            logger.error(f"Error setting up recording: {e}")
            return None

    @staticmethod
    def pause_recording(recorder):
        try:
            if hasattr(recorder, 'audio_media'):
                recorder.audio_media.stopTransmit(recorder)
                logger.info(f"Paused recording: {recorder.output_path}")
                return True
        except Exception as e:
            logger.warning(f"Pause failed: {e}")
        return False

    @staticmethod
    def resume_recording(recorder):
        try:
            if hasattr(recorder, 'audio_media'):
                recorder.audio_media.startTransmit(recorder)
                logger.info(f"Resumed recording: {recorder.output_path}")
                return True
        except Exception as e:
            logger.warning(f"Resume failed: {e}")
        return False

    @staticmethod
    def stop_recording(call, recorder=None):
        try:
            call_id = call.getInfo().callIdString
            if not recorder and call_id in audio_recorders:
                recorder = audio_recorders[call_id]
            if not recorder:
                logger.warning("No recorder found to stop")
                return False

            logger.info(f"Stopping recording for call {call_id}")
            if hasattr(recorder, 'audio_media'):
                recorder.audio_media.stopTransmit(recorder)

            try:
                if hasattr(recorder, 'close'):
                    recorder.close()
            except Exception as e:
                logger.warning(f"Error closing recorder: {e}")

            if call_id in audio_recorders:
                del audio_recorders[call_id]

            logger.info(f"Stopped recording call {call_id}")
            return True
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False
    
    @staticmethod
    def analyze_pcm_audio_level(file_path, sample_rate=8000, sample_width=2, sample_duration=1.0):
        try:
            if not os.path.exists(file_path):
                logger.warning(f"PCM file does not exist: {file_path}")
                return 0

            if sample_width not in (1, 2, 4):
                logger.warning(f"Unsupported sample width: {sample_width}")
                return 0

            dtype_map = {1: np.uint8, 2: np.int16, 4: np.int32}
            dtype = dtype_map[sample_width]

            bytes_per_sample = sample_width
            frame_count = int(sample_rate * sample_duration)
            byte_count = frame_count * bytes_per_sample

            file_size = os.path.getsize(file_path)
            if file_size < byte_count:
                logger.info(f"File too small ({file_size} bytes), adjusting window to fit")
                byte_count = file_size

            if byte_count == 0:
                logger.info("File is empty")
                return 0

            with open(file_path, 'rb') as f:
                f.seek(-byte_count, os.SEEK_END)
                raw = f.read(byte_count)

            data = np.frombuffer(raw, dtype=dtype)

            if sample_width == 1:
                data = data - 128  # convert unsigned to signed center

            if len(data) == 0:
                return 0

            rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
            return rms

        except Exception as e:
            logger.error(f"Error analyzing PCM: {e}")
            return 0


    @staticmethod
    def check_for_silence(call_id, on_silence_callback=None, on_silence_end_callback=None):
        if call_id not in audio_recorders:
            return False, 0

        recorder = audio_recorders[call_id]
        current_time = time.time()
        # Calculate time relative to recording start (in ms)
        current_ms = int((current_time - recorder.recording_start_time) * 1000)

        try:
            if current_time - recorder.last_check_time < 0.5:
                return False, 0
            recorder.last_check_time = current_time

            if not os.path.exists(recorder.output_path):
                logger.info("Audio file not found")
                return False, 0

            current_size = os.path.getsize(recorder.output_path)

            if current_size > 10000:
                rms = AudioRecorder.analyze_pcm_audio_level(recorder.output_path,
                                sample_rate=recorder.sample_rate, 
                                sample_width=recorder.sample_width, 
                                sample_duration=float(recorder.silence_duration/1000))

                recorder.volume_history.append(rms)

                if len(recorder.volume_history) > recorder.history_length:
                    recorder.volume_history.pop(0)
                
                logger.info(f"[check_for_silence] RMS: {rms:.2f}, THRESH: {recorder.silence_threshold}")

                if rms < recorder.silence_threshold:
                    # We're in a silence period
                    if recorder.silence_start_time_ms is None:
                        # First time detecting silence, record the start time
                        recorder.silence_start_time_ms = current_ms
                        
                        # If we were in speech before, record the speech segment
                        if recorder.current_speech_start_ms is not None:
                            speech_segment = {
                                'start_ms': recorder.current_speech_start_ms,
                                'end_ms': current_ms,
                                'duration_ms': current_ms - recorder.current_speech_start_ms,
                                # Calculate PCM byte position based on sample rate and width
                                'pcm_start_byte': int(recorder.current_speech_start_ms * 
                                                recorder.sample_rate * recorder.sample_width / 1000),
                                'pcm_end_byte': int(current_ms * 
                                                recorder.sample_rate * recorder.sample_width / 1000)
                            }
                            recorder.speech_segments.append(speech_segment)
                            logger.info(f"[check_for_silence] SPEECH SEGMENT RECORDED: {speech_segment['start_ms']} to {speech_segment['end_ms']} ({speech_segment['duration_ms']}ms), PCM bytes: {speech_segment['pcm_start_byte']} to {speech_segment['pcm_end_byte']}")
                            
                            # Reset speech tracking
                            recorder.current_speech_start_ms = None
                        
                        logger.info(f"[check_for_silence] SILENCE BEGAN AT: {recorder.silence_start_time_ms}ms")
                    
                    silence_duration_ms = current_ms - recorder.silence_start_time_ms
                    silence_duration = silence_duration_ms / 1000.0  # For logging in seconds
                    logger.info(f"[check_for_silence] SILENCE DETECTED: {silence_duration:.2f}s ({silence_duration_ms}ms)")
                    
                    recorder.silent_period += recorder.silence_check_interval
                    
                    logger.info(f"[check_for_silence] SILENCE STATS: current={silence_duration:.2f}s, threshold={recorder.silence_duration:.2f}s")
                    
                    if silence_duration >= recorder.silence_duration:
                        logger.info(f"[check_for_silence] SILENT EVENT ACTIVE: {silence_duration:.2f}s")
                        if not recorder.silence_detected:
                            recorder.silence_detected = True
                            logger.info(f"BEGIN SILENCE EVENT (RMS: {rms:.2f}) for call {call_id}")
                            if on_silence_callback:
                                on_silence_callback(call_id, silence_duration)
                        return True, silence_duration
                else:
                    # We're in a speech period
                    if recorder.silence_start_time_ms is not None and recorder.silence_detected:
                        silence_duration_ms = current_ms - recorder.silence_start_time_ms
                        silence_duration = silence_duration_ms / 1000.0  # For logging in seconds
                        logger.info(f"[check_for_silence] SILENCE ENDED AFTER: {silence_duration:.2f}s ({silence_duration_ms}ms)")
                        
                        # Reset silence tracking
                        if on_silence_end_callback:
                            on_silence_end_callback(call_id, silence_duration)
                    
                    # If we're starting a new speech segment after silence
                    if recorder.current_speech_start_ms is None:
                        recorder.current_speech_start_ms = current_ms
                        logger.info(f"[check_for_silence] NEW SPEECH SEGMENT STARTED AT: {recorder.current_speech_start_ms}ms")
                    
                    # Reset silence tracking
                    recorder.silence_start_time_ms = None
                    recorder.silent_period = 0
                    recorder.silence_detected = False
                    
                    logger.info("[check_for_silence] IN SPEECH EVENT")

        except Exception as e:
            logger.error(f"Error checking for silence: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return False, 0