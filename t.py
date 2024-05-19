import uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

from DeepWEBS.utilsdw.logger import logger
from DeepWEBS.networks.google_searcher import GoogleSearcher
from DeepWEBS.networks.webpage_fetcher import BatchWebpageFetcher
from DeepWEBS.documents.query_results_extractor import QueryResultsExtractor
from DeepWEBS.documents.webpage_content_extractor import BatchWebpageContentExtractor

class DeepWEBS:
    def __init__(self):
        pass

    class DeepSearch(BaseModel):
        queries: List[str] = Field(default=[""], description="Queries to search")
        result_num: int = Field(default=10, description="Number of search results")
        safe: bool = Field(default=False, description="Enable SafeSearch")
        types: List[str] = Field(default=["web"], description="Types of search results: `web`, `image`, `videos`, `news`")
        extract_webpage: bool = Field(default=False, description="Enable extracting main text contents from webpage, will add `text` field in each `query_result` dict")
        overwrite_query_html: bool = Field(default=False, description="Overwrite HTML file of query results")
        overwrite_webpage_html: bool = Field(default=False, description="Overwrite HTML files of webpages from query results")

    def queries_to_search_results(self, item: DeepSearch):
        google_searcher = GoogleSearcher()
        queries_search_results = []

        for query in item.queries:
            query_results_extractor = QueryResultsExtractor()
            if not query.strip():
                continue
            try:
                query_html_path = google_searcher.search(
                    query=query,
                    result_num=item.result_num,
                    safe=item.safe,
                    overwrite=item.overwrite_query_html,
                )
            except Exception as e:
                logger.error(f"Failed to search for query '{query}': {e}")
                continue

            try:
                query_search_results = query_results_extractor.extract(query_html_path)
            except Exception as e:
                logger.error(f"Failed to extract search results for query '{query}': {e}")
                continue

            queries_search_results.append(query_search_results)

        logger.note(queries_search_results)

        if item.extract_webpage:
            queries_search_results = self.extract_webpages(
                queries_search_results,
                overwrite_webpage_html=item.overwrite_webpage_html,
            )

        return queries_search_results

    def extract_webpages(self, queries_search_results, overwrite_webpage_html=False):
        for query_idx, query_search_results in enumerate(queries_search_results):
            try:
                batch_webpage_fetcher = BatchWebpageFetcher()
                urls = [query_result["url"] for query_result in query_search_results["query_results"]]
                url_and_html_path_list = batch_webpage_fetcher.fetch(urls, overwrite=overwrite_webpage_html, output_parent=query_search_results["query"])
            except Exception as e:
                logger.error(f"Failed to fetch webpages for query '{query_search_results['query']}': {e}")
                continue

            html_paths = [str(url_and_html_path["html_path"]) for url_and_html_path in url_and_html_path_list]
            batch_webpage_content_extractor = BatchWebpageContentExtractor()
            try:
                html_path_and_extracted_content_list = batch_webpage_content_extractor.extract(html_paths)
            except Exception as e:
                logger.error(f"Failed to extract webpage contents for query '{query_search_results['query']}': {e}")
                continue

            html_path_to_url_dict = {str(url_and_html_path["html_path"]): url_and_html_path["url"] for url_and_html_path in url_and_html_path_list}
            url_to_extracted_content_dict = {
                html_path_to_url_dict[html_path_and_extracted_content["html_path"]]: html_path_and_extracted_content["extracted_content"]
                for html_path_and_extracted_content in html_path_and_extracted_content_list
            }

            for query_result_idx, query_result in enumerate(query_search_results["query_results"]):
                url = query_result["url"]
                extracted_content = url_to_extracted_content_dict.get(url, "")
                queries_search_results[query_idx]["query_results"][query_result_idx]["text"] = extracted_content

        return queries_search_results

app = FastAPI(
    docs_url="/",
    title="Web Search API",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    version="1.0",
)

@app.get("/api/deepwebs", summary="Perform a text search using the DeepWEBS API")
def search(
    q: str = Query(..., description="The search query string"),
    max_results: int = Query(10, ge=1, le=100, description="The maximum number of results to return"),
    safesearch: str = Query("moderate", description="The safe search level ('on', 'moderate', or 'off')"),
    extract_webpage: bool = Query(False, description="Enable extracting main text contents from webpage"),
    overwrite_query_html: bool = Query(False, description="Overwrite HTML file of query results"),
    overwrite_webpage_html: bool = Query(False, description="Overwrite HTML files of webpages from query results")
):
    deepwebs = DeepWEBS()
    deep_search = DeepWEBS.DeepSearch(
        queries=[q],
        result_num=max_results,
        safe=(safesearch.lower() == 'on'),
        types=["web"],
        extract_webpage=extract_webpage,
        overwrite_query_html=overwrite_query_html,
        overwrite_webpage_html=overwrite_webpage_html,
    )
    results = deepwebs.queries_to_search_results(deep_search)
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
