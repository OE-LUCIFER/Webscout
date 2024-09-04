import requests
import uuid
import base64

# Generate a UUID for userID
user_id = str(uuid.uuid4())

# Function to encode image to base64
def encode_image_to_base64(image_path):
    with open(image_path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# Define the URL
url = 'https://artifacts.e2b.dev/api/chat'

# Define the headers
headers = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
    'content-type': 'application/json',
    'cookie': '_ga=GA1.1.176397203.1723287545; ko_id=94a6e287-f149-436b-8231-f756c4cda3f9; _ga_SCSZ10RP74=GS1.1.1723287545.1.1.1723287585.0.0.0; ph_phc_wFQaw8bTo25uDwJ4wbCE0ZhlhzcSMgcehs8kLcdvCSp_posthog=%7B%22distinct_id%22%3A%2201913bf1-2f20-7459-a2ca-7bd6fc677825%22%2C%22%24sesid%22%3A%5B1723287585765%2C%2201913bf1-2f18-7292-8ef6-93976bd08b29%22%2C1723287547672%5D%7D; ph_phc_RKpQU1ejxenHPs5x4zzAm1v8lRJFZQ60E1hRxczE6Tb_posthog=%7B%22distinct_id%22%3A%2201913bf1-c8a5-7e77-8dd3-6073d422fba6%22%2C%22%24sesid%22%3A%5B1723287597500%2C%2201913bf1-c8a1-75cf-9e51-1db79d056b03%22%2C1723287586977%5D%7D; ajs_anonymous_id=170b7a68-1f96-4f79-8533-6fa580678c02; ph_phc_4G4hDbKEleKb87f0Y4jRyvSdlP5iBQ1dHr8Qu6CcPSh_posthog=%7B%22distinct_id%22%3A%22a55a17c7-54bf-4853-b7f6-17555643bc3a%22%2C%22%24sesid%22%3A%5B1725420544684%2C%220191baf5-d33f-774b-8ac8-a5088a29338b%22%2C1725418558270%5D%2C%22%24epp%22%3Atrue%7D',
    'dnt': '1',
    'origin': 'https://artifacts.e2b.dev',
    'referer': 'https://artifacts.e2b.dev/',
    'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
}

# Define the image path
image_path = r'C:\Users\koula\OneDrive\Desktop\Webscout\photo_2024-09-03_20-12-43.jpg'

# Encode the image to base64
encoded_image = encode_image_to_base64(image_path)

# Define the payload
payload = {
    "userID": user_id,
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is this image?"},
                {"type": "image", "image": f"data:image/jpeg;base64,{encoded_image}"},
            ]
        }
    ],
    "template": {
        "code-interpreter-multilang": {
            "name": "Python data analyst",
            "lib": ["python", "jupyter", "numpy", "pandas", "matplotlib", "seaborn", "plotly"],
            "file": "script.py",
            "instructions": "Runs code as a Jupyter notebook cell. Strong data analysis angle. Can use complex visualisation to explain results.",
            "port": None
        },
        "nextjs-developer": {
            "name": "Next.js developer",
            "lib": ["nextjs@14.2.5", "typescript", "@types/node", "@types/react", "@types/react-dom", "postcss", "tailwindcss", "shadcn/ui"],
            "file": "app/page.tsx",
            "instructions": "A Next.js 13+ app that reloads automatically. Using the app router. Always add 'use client' expression on the first line of the file.",
            "port": 3000
        },
        "vue-developer": {
            "name": "Vue.js developer",
            "lib": ["vue@latest", "nuxt@3.13.0", "tailwindcss"],
            "file": "app.vue",
            "instructions": "A Vue.js 3+ app that reloads automatically. Only when asked specifically for a Vue app.",
            "port": 3000
        },
        "streamlit-developer": {
            "name": "Streamlit developer",
            "lib": ["streamlit", "pandas", "numpy", "matplotlib", "request", "seaborn", "plotly"],
            "file": "app.py",
            "instructions": "A streamlit app that reloads automatically.",
            "port": 8501
        },
        "gradio-developer": {
            "name": "Gradio developer",
            "lib": ["gradio", "pandas", "numpy", "matplotlib", "request", "seaborn", "plotly"],
            "file": "app.py",
            "instructions": "A gradio app. Gradio Blocks/Interface should be called demo.",
            "port": 7860
        }
    },
    "model": {
        "id": "gpt-4o",
        "provider": "OpenAI",
        "providerId": "openai",
        "name": "GPT-4o",
        "multiModal": True
    },
    "config": {
        "model": "gpt-4o"
    }
}

# Send the POST request
response = requests.post(url, headers=headers, json=payload)
data = response.json()["commentary"]
for item in data:
    print(item, end="", flush=True)