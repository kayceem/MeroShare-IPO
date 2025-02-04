import os
import shutil
import requests
import zipfile
from pathlib import Path

DIR_PATH = Path(__file__).parent 

def download_file(url, destination):
    """Download a file from a URL to a specified destination."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(destination, 'wb') as file:
        for chunk in response.iter_content(8192):
            file.write(chunk)

def setup_chrome_and_driver():
    """Download Chrome and ChromeDriver, and place them in a 'chrome' folder."""
    chrome_folder = Path(DIR_PATH) / "chrome"
    chrome_folder.mkdir(exist_ok=True)

    # Define URLs for Chrome and ChromeDriver for version 130.0.6723.91
    chrome_url = "https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/linux64/chrome-linux64.zip"
    chromedriver_url = "https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.91/linux64/chromedriver-linux64.zip"

    # File paths
    chrome_zip_path = chrome_folder / "chrome-linux64.zip"
    chrome_zip_folder = chrome_folder / "chrome-linux64"
    chromedriver_zip_path = chrome_folder / "chromedriver-linux64.zip"
    chromedriver_zip_folder = chrome_folder / "chromedriver-linux64"

    # Download Chrome
    print("Downloading Chrome...")
    download_file(chrome_url, chrome_zip_path)
    with zipfile.ZipFile(chrome_zip_path, 'r') as zip_ref:
        # Extract all files to a temporary location first
        zip_ref.extractall(chrome_folder)
        
        # Move contents to the main chrome_folder
        for item in chrome_zip_folder.iterdir():
            shutil.move(str(item), chrome_folder)
        chrome_zip_folder.rmdir()  # Remove temporary folder if empty

    chrome_zip_path.unlink()  # Delete zip after extraction

    # Download ChromeDriver
    print("Downloading ChromeDriver...")
    download_file(chromedriver_url, chromedriver_zip_path)
    with zipfile.ZipFile(chromedriver_zip_path, 'r') as zip_ref:
        # Extract all files to a temporary location first
        zip_ref.extractall(chrome_folder)
        
        # Move contents to the main chrome_folder
        for item in chromedriver_zip_folder.iterdir():
            shutil.move(str(item), chrome_folder)
        chromedriver_zip_folder.rmdir()  # Remove temporary folder if empty

    chromedriver_zip_path.unlink()  # Delete zip after extraction

    print(f"Chrome and ChromeDriver have been downloaded and extracted to {chrome_folder}")
    
    chrome_path = chrome_folder / "chrome"  # Update with the actual file name if different
    chromedriver_path = chrome_folder / "chromedriver"  # Update if file name is different
    chrome_crashpad_handler_path = chrome_folder / "chrome_crashpad_handler"  # Update if file name is different

    chrome_path.chmod(0o755) # Make Chrome executable
    chromedriver_path.chmod(0o755)  # Make ChromeDriver executable
    chrome_crashpad_handler_path.chmod(0o755)  # Make ChromeDriver executable

if __name__ == "__main__":
    setup_chrome_and_driver()