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
    def start_recording(call, output_path, silence_threshold=500, silence_duration=1.0):


        try:
            call_info = call.getInfo()
            call_id = call_info.callIdString
            logger.info(f"Setting up recording for call {call_id}")
            recorder = pj.AudioMediaRecorder()

            recorder.output_path = output_path
            recorder.last_size = 0
            recorder.last_check_time = time.time()
            recorder.silence_threshold = silence_threshold
            recorder.silence_duration = silence_duration
            recorder.last_active_time = time.time()
            recorder.silence_detected = False
            recorder.call_ref = call
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
    def check_for_silence(call_id, on_silence_callback=None):
        if call_id not in audio_recorders:
            return False, 0

        recorder = audio_recorders[call_id]
        current_time = time.time()

        try:
            if current_time - recorder.last_check_time < 0.5:
                return False, 0
            recorder.last_check_time = current_time

            if not os.path.exists(recorder.output_path):
                logger.info("Audio file not found")
                return False, 0

            current_size = os.path.getsize(recorder.output_path)

            if current_size == recorder.last_size:
                silence_duration = current_time - recorder.last_active_time
            else:
                recorder.last_size = current_size
                recorder.last_active_time = current_time

            if current_size > 10000:
                #AudioRecorder.pause_recording(recorder)
                rms = AudioRecorder.analyze_pcm_audio_level(recorder.output_path)
                #AudioRecorder.resume_recording(recorder)

                if not hasattr(recorder, 'volume_history'):
                    recorder.volume_history = []
                recorder.volume_history.append(rms)
                if len(recorder.volume_history) > 10:
                    recorder.volume_history.pop(0)

                avg_volume = sum(recorder.volume_history) / len(recorder.volume_history)

                logger.info(f"[check_for_silence] RMS: {rms:.2f}, AVG: {avg_volume:.2f}, THRESH: {recorder.silence_threshold}")

                if avg_volume < recorder.silence_threshold:
                    silence_duration = current_time - recorder.last_active_time
                    logger.info(f"[check_for_silence] SLENCE DETECTED: {silence_duration:.2f}s")

                    if silence_duration >= recorder.silence_duration:
                        logger.info(f"[check_for_silence] SILENT EVENT ACTIVE: {silence_duration:.2f}s")
                        if not recorder.silence_detected:
                            recorder.silence_detected = True
                            logger.info(f"BEGIN SILENCE EVENT (AVG RMS: {avg_volume:.2f}) for call {call_id}")
                            if on_silence_callback:
                                on_silence_callback(call_id, silence_duration)
                        return True, silence_duration
                else:
                    logger.info("[check_for_silence] IN SPEACH EVENT")
                    recorder.last_active_time = current_time
                    recorder.silence_detected = False

        except Exception as e:
            logger.error(f"Error checking for silence: {e}")

        return False, 0

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
