import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL = "gemini-2.5-flash"

# Create the client once at startup, not per request
client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

app = FastAPI()


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(req: ChatRequest):
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=req.message,
        config=types.GenerateContentConfig(
            system_instruction="You are a friendly, concise assistant.",
        ),
    )
    return {"reply": response.text}


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
    function add(text, cls) {
      const d = document.createElement("div");
      d.textContent = text;
      if (cls) d.className = cls;
      log.appendChild(d);
    }
    document.getElementById("f").onsubmit = async (e) => {
      e.preventDefault();
      const input = document.getElementById("m");
      const message = input.value.trim();
      if (!message) return;
      add("You: " + message, "me");
      input.value = "";
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


@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE
