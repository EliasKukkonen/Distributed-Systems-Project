import grpc
from concurrent import futures
import time
import pymongo
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Added proto directory to sys.path
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "proto"))

from proto import user_service_pb2
from proto import user_service_pb2_grpc

# MongoDB connection
mongo_client = pymongo.MongoClient("mongodb://mongodb:27017/")
db = mongo_client["userdb"]
users_collection = db["users"]

# Password hashing using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Token
SECRET_KEY = "YOUR_SECRET_KEY"  # Default is "YOUR_SECRET_KEY" for now
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    def Register(self, request, context):
        # Checks if a user with the same username already exists in the database
        if users_collection.find_one({"username": request.username}):
            return user_service_pb2.RegisterResponse(success=False, message="Username already exists.")
        
        # Hashes the password and stores the user
        hashed_password = pwd_context.hash(request.password)
        users_collection.insert_one({"username": request.username, "hashed_password": hashed_password})
        print(f"Registered new user: {request.username}")
        return user_service_pb2.RegisterResponse(success=True, message="Registration successful.")

    def Login(self, request, context):
        user = users_collection.find_one({"username": request.username})
        if user and pwd_context.verify(request.password, user["hashed_password"]):
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            token = jwt.encode({"sub": request.username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
            print(f"User logged in: {request.username}")
            return user_service_pb2.LoginResponse(success=True, message="Login successful.", token=token)
        else:
            return user_service_pb2.LoginResponse(success=False, message="Invalid username or password.", token="")

    def Exit(self, request, context):
        print(f"User exited: {request.username}")
        return user_service_pb2.ExitResponse(success=True, message="Exiting...")

def serve():
    # gRPC server with a ThreadPoolExecutor for handling multiple requests concurrently
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server is running on port 50051...")
    try:
        while True:
            time.sleep(86400)  # Default is one day
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
