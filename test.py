import requests, os, uuid, time
from datetime import datetime
from webscout import LitAgent
agent = LitAgent()
def generate_ai_art(prompt):
    url = "https://ai-api.magicstudio.com/api/ai-art-generator"
    form_data = {
        "prompt": prompt, "output_format": "bytes", "user_profile_id": "null",
        "anonymous_user_id": str(uuid.uuid4()), "request_timestamp": time.time(),
        "user_is_subscribed": "false", "client_id": uuid.uuid4().hex,
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": agent.random(),
        "Origin": "https://magicstudio.com", "Referer": "https://magicstudio.com/ai-art-generator/",
        "DNT": "1", "Sec-GPC": "1"
    }
    try:
        response = requests.post(url, data=form_data, headers=headers)
        if response.status_code == 200:
            output_dir = os.path.join(os.path.dirname(__file__), "generated_images")
            os.makedirs(output_dir, exist_ok=True)
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:30])
            filename = f"{timestamp_str}_{safe_prompt}.jpg"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"Saved to {filepath}")
            return filepath
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    prompt = input(">>> ")
    generate_ai_art(prompt)
