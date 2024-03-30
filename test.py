from webscout import DeepWEBS


def perform_web_search(query):
    D = DeepWEBS() 
    item = D.DeepSearch(
        queries=[query],  # Query to search
        result_num=5,  # Number of search results
        safe=True,  # Enable SafeSearch
        types=["web"],  # Search type:  web
        extract_webpage=True, # True for extracting webpages
        overwrite_query_html=False,
        overwrite_webpage_html=False,
    )
    results = D.queries_to_search_results(item)

    return results

def print_search_results(results):
    """
    Print the search results.
    
    Args:
    - search_results (list): List of search results to print.
    """
    if results:
        for index, result in enumerate(results, start=1):
            print(f"Result {index}: {result}")
    else:
        print("No search results found.")

def main():
    query = input("Enter your search query: ")
    results = perform_web_search(query)
    print_search_results(results)

if __name__ == "__main__":
    main()
