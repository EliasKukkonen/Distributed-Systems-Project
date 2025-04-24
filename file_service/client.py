import requests
import os

FILE_SERVICE_URL = "http://localhost:50053"

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

def run_file_service():
    while True:
        print("\nFile Service Menu:")
        print("1. Upload file")
        print("2. Download file")
        print("3. Back to Chat Service")
        choice = input("Your choice: ")
        
        if choice == "1":
            file_path = input("Enter file path to upload (e.g., example.txt): ")
            upload_file(file_path)
        elif choice == "2":
            file_id = input("Enter file ID to download: ")
            output_path = input("Enter output path (e.g., downloaded_file.txt): ")
            download_file(file_id, output_path)
        elif choice == "3":
            print("Returning to Chat Service...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    run_file_service()