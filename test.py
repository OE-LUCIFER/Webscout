from webscout import WEBS

R = WEBS().text("python programming", max_results=5)
print(R)