import requests
import re
import urllib.parse

url = "http://localhost:5000/fill-template"
files = {"file": open("templater/example.docx", "rb")}
data = {"city": "חריש"}

response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    content_disposition = response.headers.get("Content-Disposition", "")
    filename = "templater/output.docx"
    # Try to extract UTF-8 filename (RFC 5987)
    match = re.search(r"filename\*=UTF-8''(.+)", content_disposition)
    if match:
        filename = urllib.parse.unquote(match.group(1))
    elif "filename=" in content_disposition:
        filename = content_disposition.split("filename=")[-1].strip('";')
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"File saved as {filename}")
else:
    print("Error:", response.json())