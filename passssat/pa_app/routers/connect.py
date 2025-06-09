import os
import socket

from pydantic import BaseModel

from fastapi import (
    APIRouter, 
    Request)

router = APIRouter(
    prefix="",
    tags=[""]
)

class ExampleForm(BaseModel):
    message: str

def conn_and_send(message):
    HOST = os.getenv("HOST", "127.17.0.1")
    # HOST = os.getenv("HOST", "host.docker.internal")
    PORT = int(os.getenv("PORT", 42069))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        print(f"Connected to server at {HOST}:{PORT}")

        s.sendall(message.encode())
        print(f"Sent: {message}")

        print("Closing connection.")


@router.post("/con_and_send")
async def save_message(data: ExampleForm):
    message = data.message
    conn_and_send(message)
    return f"Message: {message} - SEND"