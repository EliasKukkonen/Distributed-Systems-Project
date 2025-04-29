import grpc
from concurrent import futures
import time
import jwt
import sys, os

# Import generated gRPC classes
from chat_service_pb2 import EnterChatResponse, LogoutResponse
import chat_service_pb2_grpc

# JWT settings (shared with user_service for authentication)
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
ALGORITHM = "HS256"

# In-memory store to hold active user tokens (can be scaled to Redis etc.)
active_tokens = set()

# Define the ChatService server implementation
class ChatServiceServicer(chat_service_pb2_grpc.ChatServiceServicer):
    # Handle user entry into chat after validating token
    def EnterChat(self, request, context):
        token = request.token
        try:
            # Decode JWT to verify authenticity and expiration
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Register token as active if valid
            if token not in active_tokens:
                active_tokens.add(token)
            username = payload.get("sub", "Unknown")
            return EnterChatResponse(success=True, message=f"Welcome to the chat, {username}!")
        except jwt.ExpiredSignatureError:
            return EnterChatResponse(success=False, message="Token has expired.")
        except jwt.InvalidTokenError:
            return EnterChatResponse(success=False, message="Invalid token.")

    # Handle user logout and token invalidation
    def Logout(self, request, context):
        token = request.token
        if token in active_tokens:
            active_tokens.remove(token)
            return LogoutResponse(success=True, message="\nLogout successful, token invalidated.")
        else:
            return LogoutResponse(success=False, message="\nToken not found or already logged out.")

# Start and run the gRPC server
def serve():
    # Create a gRPC server with thread pool for concurrency (handles multiple users)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_service_pb2_grpc.add_ChatServiceServicer_to_server(ChatServiceServicer(), server)
    server.add_insecure_port('[::]:50052')  # Different port than user_service
    server.start()
    print("Chat service is running on port 50052...")
    try:
        while True:
            # Keep server alive indefinitely
            time.sleep(86400)
    except KeyboardInterrupt:
        # Gracefully stop server on Ctrl+C
        server.stop(0)

# Entry point to launch the server
if __name__ == '__main__':
    serve()
