import os
from dotenv import load_dotenv

load_dotenv()  


print("This is a test file to check if the import works correctly.")

print(os.getenv("APIKEYS"))