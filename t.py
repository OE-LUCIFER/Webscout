from webscout import WEBS

# Instant answers for the query "sun" using DuckDuckGo.com 
with WEBS() as webs:
    for r in webs.answers("sun"):
        print(r)