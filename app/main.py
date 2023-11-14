from fastapi import FastAPI, HTTPException
from typing import List, Optional
from app.services.LLM.gpt4_vision import chatgpt
from app.db.schemas import ChatInput

app = FastAPI()

@app.post("/chatGPT")
def chatGPT(user_input: ChatInput):

    # No need to decode the images
    print("text", user_input.text)
    print("image", user_input.images)
    input_data = chatgpt.format_input(user_input.text, user_input.images)
    print("-"*220, input_data)

    response_text = chatgpt.chat_with_gpt(input_data)
    chatgpt.construct_history(previous_output = response_text)
    print(response_text)
    return {"response":response_text}

