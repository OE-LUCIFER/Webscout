import requests
from rich import print

def WEBSX(query):
    url = 'https://searx.bnngpt.com/api/v1/scrape/'
    data = {'query': query}
    response = requests.post(url, data=data)
    responses = response.json().get('responses')
    return responses

if __name__ == "__main__":
    # Example search query
    search_query = "Python development tools"
    
    # Call the WEBSX function with the search query
    result = WEBSX(search_query)
    
    # Pretty-print the JSON response
    print(result)