import json
from webscout import DeepInfraImager
bot = DeepInfraImager()
resp = bot.generate("AI-generated image - webscout", 1)
print(bot.save(resp))
#------------------------------------------------------
from webscout import PollinationsAI
bot = PollinationsAI()
resp = bot.generate("AI-generated image - webscout", 1)
print(bot.save(resp))
#--------------------TTS---------------------------
from webscout import Voicepods
voicepods = Voicepods()
text = "Hello, this is a test of the Voicepods text-to-speech"

print("Generating audio...")
audio_file = voicepods.tts(text)

print("Playing audio...")
voicepods.play_audio(audio_file)
#------------------------------------------------------
from webscout import StreamElements
stream = StreamElements()
text = "Hello, this is a test of the StreamElements text-to-speech"
a = stream.tts(text, voice="Brian")
stream.play_audio(a)