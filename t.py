
from webscout import TalkaiImager


bot = TalkaiImager()
try:
    resp = bot.generate("A shiny red sports car speeding down a scenic mountain road", 1)
    print(bot.save(resp))
except Exception as e:
    print(f"An error occurred: {e}")