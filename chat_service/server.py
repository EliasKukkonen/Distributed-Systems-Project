import grpc
from concurrent import futures
import time
import jwt
import sys, os

from chat_service_pb2 import EnterChatResponse, LogoutResponse
import chat_service_pb2_grpc

# Same secret key as in user_service so tokens can be validated
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
ALGORITHM = "HS256"

# Holds active tokens
active_tokens = set()

class ChatServiceServicer(chat_service_pb2_grpc.ChatServiceServicer):
    def EnterChat(self, request, context):
        token = request.token
        try:
            # Validates the token using JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Adds token to active tokens if not already present
            if token not in active_tokens:
                active_tokens.add(token)
            username = payload.get("sub", "Unknown")
            return EnterChatResponse(success=True, message=f"Welcome to the chat, {username}!")
        except jwt.ExpiredSignatureError:
            return EnterChatResponse(success=False, message="Token has expired.")
        except jwt.InvalidTokenError:
            return EnterChatResponse(success=False, message="Invalid token.")

    def Logout(self, request, context):
        token = request.token
        if token in active_tokens:
            active_tokens.remove(token)
            return LogoutResponse(success=True, message="Logout successful. Token invalidated.")
        else:
            return LogoutResponse(success=False, message="Token not found or already logged out.")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_service_pb2_grpc.add_ChatServiceServicer_to_server(ChatServiceServicer(), server)
    server.add_insecure_port('[::]:50052')  # Different port than user_service
    server.start()
    print("Chat Service is running on port 50052...")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
