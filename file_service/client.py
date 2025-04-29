import requests
import os

# Base URL for file service
FILE_SERVICE_URL = "http://localhost:50053"

# Upload a file to the file service
def upload_file(file_path):
    url = f"{FILE_SERVICE_URL}/files/upload"
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = requests.post(url, files=files)
        if response.status_code == 200:
            print("Upload successful:", response.json())
            return response.json().get("file_id")
        else:
            print("Upload failed:", response.text)
            return None
    except FileNotFoundError:
        print(f"File {file_path} not found")
        return None
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

# Download a file from the file service
def download_file(file_id, output_path):
    url = f"{FILE_SERVICE_URL}/files/{file_id}/download"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"File downloaded to {output_path}")
        else:
            print("Download failed:", response.text)
    except Exception as e:
        print(f"Error downloading file: {e}")

# Menu-driven interface for file operations
def run_file_service():
    try:
        while True:
            # Display file service menu
            print("\nFile service menu:")
            print("1. Upload file")
            print("2. Download file")
            print("3. Return")
            choice = input("Your choice: ")
        
            if choice == "1":
                file_path = input("Enter file path to upload (e.g., example.txt): ")
                upload_file(file_path)
            elif choice == "2":
                file_id = input("Enter file ID to download: ")
                output_path = input("Enter output path (e.g., downloaded_file.txt): ")
                download_file(file_id, output_path)
            elif choice == "3":
                # Return to chat service
                print("\nReturning to chat service...")
                break
            else:
                print("Invalid choice, please try again.")
    except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\nReturning to chat service...")

# Entry point for testing or standalone usage
if __name__ == "__main__":
    run_file_service()