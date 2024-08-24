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
#------------------------------------------------------
