##Testing the TTS component

from SinisterSixSystems.components.tts import TTS

tts = TTS()

tts.generate_batch_audio([
    {"voice": "alba", "text": "Hey, did you hear about photosynthesis?"},
    {"voice": "eponine", "text": "Yes, it's the process by which plants make their own food using sunlight."},
    {"voice": "alba", "text": "Exactly! They convert carbon dioxide and water into glucose and oxygen."},
    {"voice": "eponine", "text": "It's amazing how chlorophyll absorbs light energy for this reaction."},
    {"voice": "alba", "text": "Do you know why plants look green?"},
    {"voice": "eponine", "text": "Because chlorophyll reflects green wavelengths!"},
    {"voice": "alba", "text": "Biology can be so fascinating, especially topics like mitochondria and cellular respiration."},
    {"voice": "eponine", "text": "True! Without these processes, life on Earth wouldn't exist."}
])