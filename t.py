from webscout import WEBSX

def main():
    # Initialize the WEBSX client
    search = WEBSX(
        k=10,  
    )

    # Example using `run` method - Get a summary
    query = "What is the capital of France?"
    answer = search.run(query)
    print(f"Answer: {answer}\n")

    # Example using `results` method - Get detailed results with metadata
    query = "What is the capital of France?"
    results = search.results(query, num_results=3)
    print("Search Results:")
    for result in results:
        print(f"Title: {result['title']}")
        print(f"Snippet: {result['snippet']}")
        print(f"Link: {result['link']}\n")
        print(f'Engines: {result["engines"]}')


if __name__ == "__main__":
    main()