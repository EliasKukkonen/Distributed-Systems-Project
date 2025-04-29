import grpc
import sys
import os

# Set up Python path to find generated proto modules and other services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "proto"))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import generated proto classes for user service communication
from proto import user_service_pb2
from proto import user_service_pb2_grpc

# Import chat service client to allow transition after login
from chat_service.client import run_chat

# Function to run the user service client
def run_user_service_client():
    # Establish insecure gRPC channel to the user service server
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = user_service_pb2_grpc.UserServiceStub(channel)
        token = ""
        try:
            while True:
                # Display user service menu
                print("\nUser service menu:")
                print("1. Register")
                print("2. Login")
                print("3. Exit")
                choice = input("Your choice: ")

                if choice == "1":
                    # Handle user registration
                    username = input("Username: ")
                    password = input("Password: ")
                    response = stub.Register(user_service_pb2.RegisterRequest(username=username, password=password))
                    print(response.message)
                elif choice == "2":
                    # Handle user login and transition to chat service if successful
                    username = input("Username: ")
                    password = input("Password: ")
                    response = stub.Login(user_service_pb2.LoginRequest(username=username, password=password))
                    print(response.message)
                    if response.success:
                        token = response.token
                        run_chat(token)
                elif choice == "3":
                    # Exit the user service client
                    print("\nExiting user service...")
                    break
                else:
                    # Handle invalid input
                    print("Invalid choice, please try again.")
        except KeyboardInterrupt:
                # Handle Ctrl+C interruption gracefully
                print("\n\nExiting user service...")

# Entry point to start the client
if __name__ == '__main__':
    run_user_service_client()