import requests
import json
import os

def main():
    # Define the API endpoint
    url = "https://www.ninjachat.ai/api/image-generator"

    # Define the headers
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
        "Content-Type": "application/json",
        "DNT": "1",
        "Origin": "https://www.ninjachat.ai",
        "Priority": "u=1, i",
        "Referer": "https://www.ninjachat.ai/image-generation",
        "Sec-CH-UA": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }

    # Define the payload
    payload = {
        "prompt": "blue car",
        "model": "stable-diffusion", #
        "negativePrompt": "",
        "cfg": 7,
        "aspectRatio": "1:1",
        "outputFormat": "png",
        "numOutputs": 1,
        "outputQuality": 90
    }

    try:
        # Make the POST request
        response = requests.post(url, headers=headers, json=payload)

        # Check the response status
        if response.status_code == 200:
            data = response.json()
            print(data)
            image_urls = data.get('output', [])
            
            if not image_urls:
                print("No images were returned in the response.")
                return

            for idx, img_url in enumerate(image_urls):
                # Download the image
                img_response = requests.get(img_url)
                
                if img_response.status_code == 200:
                    image_filename = f"output_image_{idx + 1}.{payload['outputFormat']}"
                    with open(image_filename, "wb") as f:
                        f.write(img_response.content)
                    print(f"Image {idx + 1} downloaded successfully: {image_filename}")
                else:
                    print(f"Failed to download image {idx + 1} from {img_url}")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print("Response Content:", response.text)

    except requests.exceptions.RequestException as e:
        print("An error occurred while making the request:", e)

if __name__ == "__main__":
    main()