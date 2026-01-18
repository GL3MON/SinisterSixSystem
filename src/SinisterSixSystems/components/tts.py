from SinisterSixSystems.logging import logger
from SinisterSixSystems.config import TTSConfig
from pocket_tts import TTSModel
import numpy as np

import torch
import scipy.io.wavfile


class TTS:
    def __init__(self) -> None:
        self.model = TTSModel.load_model()
        self.config = TTSConfig()

    def generate_audio(self, text: str, voice: str) -> None:
        try:
            voice_state = self.model.get_state_for_audio_prompt(voice)
            audio = self.model.generate_audio(voice_state, text, frames_after_eos=2)
        except Exception as e:
            logger.warning(f"Error generating audio: {e}")
            if "We could not download the weights for the model with voice cloning" in str(e):
                logger.warning("Voice cloning is not available, using default voice")
                audio = self.model.generate_audio("alba", text)
            else:
                raise e

        scipy.io.wavfile.write(self.config.default_audio_path, self.model.sample_rate, audio.numpy())

    def generate_batch_audio(self, conversations: list[dict[str, str]]) -> None:
        audios = []
        silence_duration_seconds = np.random.uniform(0.1, 0.3)
        try:
            for conversation in conversations:
                voice, text = conversation["voice"], conversation["text"]
                voice_state = self.model.get_state_for_audio_prompt(voice)
                audio = self.model.generate_audio(voice_state, text, frames_after_eos=2)
                audios.append(audio)
        except Exception as e:
            logger.error(f"Error generating batch audio: {e}")
            if "We could not download the weights for the model with voice cloning" in str(e):
                logger.warning("Voice cloning is not available, using default voice")
                for conversation in conversations:
                    voice, text = conversation["voice"], conversation["text"]
                    voice_state = self.model.get_state_for_audio_prompt("alba")
                    audio = self.model.generate_audio(voice_state, text, frames_after_eos=2)
                    audios.append(audio)
            else:
                raise e

        # Prepare silence tensor
        sample_rate = self.model.sample_rate
        # Check if audio is 1D or 2D
        audio_shape = audios[0].shape
        if len(audio_shape) == 1:
            # 1D audio: (num_samples,)
            silence_samples = int(silence_duration_seconds * sample_rate)
            silence = torch.zeros(silence_samples, dtype=audios[0].dtype, device=audios[0].device)
            concat_dim = 0
        else:
            # 2D audio: (num_channels, num_samples)
            num_channels = audio_shape[0]
            silence_samples = int(silence_duration_seconds * sample_rate)
            silence = torch.zeros((num_channels, silence_samples), dtype=audios[0].dtype, device=audios[0].device)
            concat_dim = 1

        # Interleave silence between audios
        merged_audio = []
        for idx, audio in enumerate(audios):
            merged_audio.append(audio)
            # Don't add silence after the last segment
            if idx < len(audios) - 1:
                merged_audio.append(silence)

        final_audio = torch.cat(merged_audio, dim=concat_dim)
        scipy.io.wavfile.write(self.config.default_audio_path, sample_rate, final_audio.cpu().numpy())