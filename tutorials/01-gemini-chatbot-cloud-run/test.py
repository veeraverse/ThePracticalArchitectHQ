import os
from google import genai

client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain Google Cloud Run in one sentence.",
)
print(response.text)
