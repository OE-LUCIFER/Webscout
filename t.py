from webscout import VLM

vlm = VLM(model="llava-hf/llava-1.5-7b-hf", system_prompt="You are a helpful and informative AI assistant.")

# Path to the image and the user message
image_path = r"C:\Users\hp\Desktop\main\photo_2024-05-15_15-23-52.jpg"
user_message = "What is shown in this image?"

# Encode the image to base64
image_base64 = vlm.encode_image_to_base64(image_path)

# Define the prompt with both image and text
prompt = {
    "role": "user",
    "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
        {"type": "text", "text": user_message}
    ]
}

# Get the response
response = vlm.ask(prompt)

# Extract and print the message from the response
message = vlm.get_message(response)
print(message)