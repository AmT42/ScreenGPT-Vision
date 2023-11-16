from fastapi import FastAPI, HTTPException
from typing import List, Optional
from app.services.LLM.gpt4_vision import chatgpt
from app.db.schemas import ChatInput

app = FastAPI()

@app.post("/chatGPT")
def chatGPT(user_input: ChatInput):

    # put input received from the front to the right format
    input_data = chatgpt.format_input(user_input.text, user_input.images)

    # get gpt response
    response_text = chatgpt.chat_with_gpt(input_data)

    # add message to the chat history
    chatgpt.construct_history(previous_output = response_text)
    return {"response":response_text}

