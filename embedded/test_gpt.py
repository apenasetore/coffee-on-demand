import openai
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
client = openai.OpenAI(api_key=API_KEY)

response = client.chat.completions.create(
    model="gpt-4o-mini-audio-preview",
    messages="Olá, este é um teste de geração de áudio usando a OpenAI! Diga olá para o Panda Penguin",
    modalities=["text", "audio"]
)

# Salvar o áudio como um arquivo MP3
with open("output.mp3", "wb") as f:
    f.write(response.content)

print("Áudio gerado e salvo como output.mp3")