import grpc

# Added proto directory to sys.path
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "proto"))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from proto import user_service_pb2
from proto import user_service_pb2_grpc
from chat_service.chat_client import run_chat

def run_user_service_client():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = user_service_pb2_grpc.UserServiceStub(channel)
        token = ""
        while True:
            print("\nSelect an option:")
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            choice = input("Your choice: ")

            if choice == "1":
                username = input("Username: ")
                password = input("Password: ")
                response = stub.Register(user_service_pb2.RegisterRequest(username=username, password=password))
                print(response.message)
            elif choice == "2":
                username = input("Username: ")
                password = input("Password: ")
                response = stub.Login(user_service_pb2.LoginRequest(username=username, password=password))
                print(response.message)
                if response.success:
                    token = response.token
                    print("JWT token:", token)
                    # Once logged in, automatically transition to chat_service with run_chat functionality
                    run_chat(token)
                    break
            elif choice == "3":
                username = input("Username: ")
                response = stub.Exit(user_service_pb2.ExitRequest(username=username))
                print(response.message)
                break
            else:
                print("Invalid choice, please try again.")

if __name__ == '__main__':
    run_user_service_client()