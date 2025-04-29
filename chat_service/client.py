import grpc
import sys
import os

# Add paths to import other services and generated proto modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../file_service')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../messaging_service")))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "proto"))

# Import generated proto classes
from chat_service_pb2 import EnterChatRequest, LogoutRequest
from chat_service_pb2_grpc import ChatServiceStub

# Import file and messaging services
from file_service.client import run_file_service
from messaging_service.client import run_messaging_ui

# Function to run the chat service client
def run_chat(token):
    with grpc.insecure_channel('localhost:50052') as channel:  # Docker-verkon osoite
        stub = ChatServiceStub(channel)
        # Send the token to verify login
        response = stub.EnterChat(EnterChatRequest(token=token))
        if not response.success:
            print("Access denied:", response.message)
            return
        print(response.message)
        # Placeholder menu with logout and file service options
        try:
            while True:
                # Display chat service menu
                print("\nChat service menu:")
                print("1. Messaging service")
                print("2. File service")
                print("3. Logout")
                choice = input("Your choice: ")
                if choice == "1":
                    # Enter messaging service (real-time chatting)
                    run_messaging_ui(token) 
                elif choice == "2":
                    # Enter file service (for file uploads/downloads)
                    run_file_service()
                elif choice == "3":
                    # Logout cleanly and return to user service
                    logout_response = stub.Logout(LogoutRequest(token=token))
                    print(logout_response.message)
                    print("Returning to user service...")
                    break
                else:
                    # Handle invalid user input
                    print("Invalid choice, please try again.")
        except KeyboardInterrupt:
            # Handle Ctrl+C by logging out safely
            logout_response = stub.Logout(LogoutRequest(token=token))
            print(f"\n{logout_response.message}")
            print("Returning to user service...")

# Entry point to run client directly
if __name__ == '__main__':
    token = input("Enter your JWT token: ")
    run_chat(token)
