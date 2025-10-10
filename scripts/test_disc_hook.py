import requests

webhook_url = "https://discord.com/api/webhooks/1426198786807562372/_hpF-HBB_Z5lrygyRqRDrObTcrwqJYpiPYreoQXZFcV-VD-zC_EOOxfI_jE05sk022Ju"

data = {
    "content": "Hello from Python! 🎉"
}

response = requests.post(webhook_url, json=data)

if response.status_code == 204:
    print("Message sent successfully!")
else:
    print(f"Failed to send message: {response.status_code}, {response.text}")
