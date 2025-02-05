import base64
import io
import json
import os
import time
import openai
from dotenv import load_dotenv
from pydantic import BaseModel
import pygame


class GPTInteraction(BaseModel):
    response: str
    chosen_coffee_weight: int = None
    container_number: int = None
    total_price: float = None
    order_confirmed: bool = None


phases = [
    {
        "name": "IntroductionState",
        "goal": "Greet the user warmly and understand their initial needs.",
        "guideline": "Welcome the user with a friendly greeting. If their name is known, address them personally (e.g., 'Hello, [name]!'). Ask how you can assist with their coffee selection or purchase. Do not make topics, be concise",
    },
    {
        "name": "AvailableCoffeeState",
        "goal": "Provide information about the available coffee options and help the user make a choice.",
        "guideline": "Ask the user which coffee type they prefer. If requested, provide descriptions of the available options. If the user is registered, suggest coffee options based on their purchase history. Ensure your suggestions are clear and concise. Do not make topics, be concise",
    },
    {
        "name": "QuantityState",
        "goal": "Determine how much coffee the user wants to purchase.",
        "guideline": "Ask the user to specify the quantity of coffee they would like, within the range of 20 to 300 grams. Verify stock availability and provide feedback if the desired quantity exceeds the available stock. If necessary, suggest alternative quantities.Do not make topics, be concise",
    },
    {
        "name": "OrderConfirmationState",
        "goal": "Confirm the user's coffee selection and proceed to the finished phase.",
        "guideline": "Summarize the user's order, including the chosen coffee type, quantity, and total price. Ask for confirmation to proceed with the order and explain the next steps, such as generating a payment QR code.Do not make topics, be concise",
    },
    {
        "name": "FinishedState",
        "goal": "You have not said goodbye to the user after the order confirmation",
        "guideline": "Once the user confirms the order, provide a final thank you message and conclude the conversation without any additional prompts or questions. Ensure that this state marks the complete fulfillment of the order process by returning `inPhase = False` to indicate that the goal is fully achieved.",
    },
    {
        "name": "Incompatible",
        "goal": "Politely redirect the user back to coffee-related topics if the conversation strays.",
        "guideline": "If the user discusses unrelated topics, gently bring the conversation back to coffee options or services. Example: 'I specialize in coffee selections and purchases. Would you like to explore our coffee varieties?'",
    },
]

main_prompt = f"""You are a coffee vending machine that sells coffee grains. Follow the instructions below:  
    - You are selling in Reais, Brazil's currency. But always speak in English.
    - Coffee price is calculated per gram (provide the total price).
    - Coffees available: Liberica (container 1, price: R$0,20/g), Arabica (container 2, price: R$0,25/g), Constantino (container 3, price: R$0,30/g) and Robusta (container 4, price: R$0,15/g).
    - Your task is to analyze the conversation history and identify in what phase it is
    - Phases of conversation: {phases}
    - Answer in an concise way, very small text, without topics and do not use '/' or '*' in answer.
    
    Additional details:
    - Client's name: Panda Penguim
    - Purchase history: This client has no purchase history."""

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("API_KEY"))

conversation_history = []
while True:
    print("Requesting GPT audio")
    start = time.perf_counter()
    messages = [
        {
            "role": "system",
            "content": main_prompt,
        },
    ]
    messages.extend(conversation_history)
    gpt_audio_response = client.chat.completions.create(
        model="gpt-4o-mini-audio-preview",
        messages=messages,
        modalities=["text", "audio"],
        audio={
            "voice": "sage",
            "format": "mp3",
        },
        timeout=10,
    )

    transcription = gpt_audio_response.choices[0].message.audio.transcript
    conversation_history.append(
        {
            "role": "assistant",
            "content": gpt_audio_response.choices[0].message.audio.id,
        }
    )
    print(f"Audio response: {transcription}")
    print(f"Time waiting for GPT audio response {time.perf_counter() - start}s")

    second_prompt = """You are a conversation analyzer of a coffee vending machine and a customer.
        You need to read the conversation check if all necessary information has been gotten.
        Remember to fill obrigatory fields:
        
        - chosen_coffee_weight
        - container_number (is the number of the container where the chosen coffee is located at)
        - total_price
        - order_confirmed (if and only if the client confirm its order. Do not set it as true if assistant ask and the client didnt answer)"""

    second_messages = [
        {"role": "system", "content": second_prompt},
        {
            "role": "user",
            "content": f"The conversation is this: {conversation_history}",
        },
    ]

    start = time.perf_counter()

    gpt_interaction_variables = client.beta.chat.completions.parse(
        model="gpt-4o-mini", messages=second_messages, response_format=GPTInteraction
    )
    gpt_interaction_variables_object = json.loads(
        gpt_interaction_variables.choices[0].message.content
    )
    print(GPTInteraction(**gpt_interaction_variables_object))

    print(f"Time waiting for GPT text response {time.perf_counter() - start}s")

    start = time.perf_counter()

    audio_base64 = gpt_audio_response.choices[0].message.audio.data
    audio_bytes = base64.b64decode(audio_base64)
    audio_buffer = io.BytesIO(audio_bytes)

    print(f"Time waiting for base64 decode {time.perf_counter() - start}s")

    start = time.perf_counter()

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    pygame.mixer.music.load(audio_buffer, "mp3")
    pygame.mixer.music.play()

    print(f"Time waiting for pyaudio {time.perf_counter() - start}s")

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

    response = input("Type response: ")
    conversation_history.append({"role": "user", "content": response})
