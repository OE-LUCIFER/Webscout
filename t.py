from webscout import WEBS

# Text search for 'live free or die' using DuckDuckGo.com 
with WEBS() as WEBS:
    for r in WEBS.text('live free or die', region='wt-wt', safesearch='off', timelimit='y', max_results=10, backend='lite'):
        print(r)