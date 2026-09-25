import os
import re
from google import genai
from google.genai import types

def convert():
    try:
        client = genai.Client()
        print("Client initialized successfully.")
    except Exception as e:
        print("Failed to initialize client:", e)

convert()
