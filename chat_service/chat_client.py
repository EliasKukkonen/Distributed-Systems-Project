import grpc
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../file_service')))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "proto"))

from chat_service_pb2 import EnterChatRequest, LogoutRequest
from chat_service_pb2_grpc import ChatServiceStub
from file_service.client import run_file_service

def run_chat(token):
    with grpc.insecure_channel('localhost:50052') as channel:  # Docker-verkon osoite
        stub = ChatServiceStub(channel)
        # Verify token and enter chat
        response = stub.EnterChat(EnterChatRequest(token=token))
        if not response.success:
            print("Access denied:", response.message)
            return
        print(response.message)
        # Placeholder menu with logout and file service options
        try:
            while True:
                print("\nMenu:")
                print("1. Placeholder action")
                print("2. File Service")
                print("3. Logout")
                choice = input("Your choice: ")
                if choice == "1":
                    print("Placeholder action executed.")
                elif choice == "2":
                    run_file_service()
                elif choice == "3":
                    logout_response = stub.Logout(LogoutRequest(token=token))
                    print(logout_response.message)
                    break
                else:
                    print("Invalid choice. Please try again.")
        except KeyboardInterrupt:
            # Handle Ctrl+C by logging out
            print("\nInterrupt received. Logging out...")
            logout_response = stub.Logout(LogoutRequest(token=token))
            print(logout_response.message)

if __name__ == '__main__':
    token = input("Enter your JWT token: ")
    run_chat(token)
