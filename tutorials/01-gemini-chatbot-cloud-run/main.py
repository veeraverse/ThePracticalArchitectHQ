"""A minimal Gemini chatbot served by FastAPI, ready to deploy on Cloud Run.

Two routes:
  GET  /      -> a tiny HTML chat page
  POST /chat  -> sends the user's message to Gemini and returns the reply

Required env vars:
  GOOGLE_CLOUD_PROJECT   the GCP project that has Vertex AI enabled
  GOOGLE_CLOUD_LOCATION  (optional) Vertex AI region, defaults to us-central1
"""

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types
from pydantic import BaseModel

# Fast, low-cost model that suits a chat demo. Swap for a larger model if needed.
MODEL = "gemini-2.5-flash"

# Create the client once at startup, not per request.
# vertexai=True routes calls through Vertex AI, so on Cloud Run the service
# account's credentials are used automatically (no API key to manage).
client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

app = FastAPI()


# Shape of the JSON body POSTed to /chat, e.g. {"message": "Hello"}.
# Pydantic validates it and FastAPI returns a 422 if it doesn't match.
class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    # Use the async client (client.aio) so a slow model call doesn't block
    # other requests being handled by the same Cloud Run instance.
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=req.message,
        config=types.GenerateContentConfig(
            # The system instruction sets the assistant's tone for every reply.
            system_instruction="You are a friendly, concise assistant.",
        ),
    )
    # Each request is independent: no chat history is kept between messages.
    return {"reply": response.text}


# The whole front end lives in this one string so the tutorial stays a single
# file. The page posts to /chat and appends each reply to the log.
PAGE = """
<!doctype html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gemini Chatbot</title>
  <style>
    body { font-family: sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; }
    #log div { margin: 8px 0; }
    .me { font-weight: bold; }
    form { display: flex; gap: 8px; }
    input { flex: 1; padding: 8px; }
  </style>
</head>
<body>
  <h1>Gemini Chatbot</h1>
  <div id="log"></div>
  <form id="f">
    <input id="m" placeholder="Ask me anything" autocomplete="off">
    <button>Send</button>
  </form>
  <script>
    const log = document.getElementById("log");

    // Append a line to the chat log. textContent (not innerHTML) keeps
    // model output from being interpreted as HTML.
    function add(text, cls) {
      const d = document.createElement("div");
      d.textContent = text;
      if (cls) d.className = cls;
      log.appendChild(d);
    }

    document.getElementById("f").onsubmit = async (e) => {
      e.preventDefault(); // stop the browser from reloading the page
      const input = document.getElementById("m");
      const message = input.value.trim();
      if (!message) return;
      add("You: " + message, "me");
      input.value = "";

      // Send the message to our FastAPI backend and show Gemini's reply.
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      add("Gemini: " + data.reply);
    };
  </script>
</body>
</html>
"""


# Serve the chat page at the root URL.
@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE
