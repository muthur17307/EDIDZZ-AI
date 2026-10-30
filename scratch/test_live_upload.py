import urllib.request

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = (
    f"--{boundary}\r\n"
    'Content-Disposition: form-data; name="files"; filename="clip1.mp4"\r\n'
    "Content-Type: video/mp4\r\n\r\n"
    "fake video data 1\r\n"
    f"--{boundary}\r\n"
    'Content-Disposition: form-data; name="files"; filename="clip2.mp4"\r\n'
    "Content-Type: video/mp4\r\n\r\n"
    "fake video data 2\r\n"
    f"--{boundary}--\r\n"
).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/media/upload/batch",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=5.0) as resp:
        print("POST /api/media/upload/batch ->", resp.status, resp.read().decode())
except Exception as e:
    print("POST /api/media/upload/batch -> ERROR:", e)

