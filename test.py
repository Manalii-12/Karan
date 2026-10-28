import requests

r = requests.get("https://www.googleapis.com/gmail/v1/users/me/profile")
print(r.status_code)

