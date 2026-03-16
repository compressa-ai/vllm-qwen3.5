import requests
import json

response = requests.post(
  url="http://localhost:10010/v1/chat/completions",
  headers={
    "Authorization": "Bearer TOKEN_1",
    "accept": "application/json",
    "Content-Type": "application/json"
  },
  json={
    "model": "Qwen/Qwen3.5-35B-A3B-FP8",
    "messages": [
      {
        "role": "system",
        "content": "You are a conspiracy theorist."
      },
      {
        "role": "user",
        "content": "Prove to me that the Americans were not on the moon."
      }
    ],
    "max_tokens": 4096,
    "temperature": 0.5,
    "stream": True,
    "chat_template_kwargs": {"enable_thinking": False},
  }, 
  stream=True
)
print(f"Status code: {response.status_code}\n--- STREAM START ---")

for line in response.iter_lines(decode_unicode=True):
    if line:
        if line == "data: [DONE]":
            print("\n\n--- STREAM DONE ---")
            break
        elif line.startswith("data: "):
            try:
                line = json.loads(line[6:])
                try:
                    print(line["choices"][0]["delta"]["content"], end="", flush=True)
                except:
                    print(line, end="", flush=True)
            except json.JSONDecodeError:
                print(line, end="", flush=True)
        else:
            print(line, end="", flush=True)