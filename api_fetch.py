#!/usr/bin/env python3
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
CITY = os.getenv("CITY")

if not API_KEY or not CITY:
    print("Missing API_KEY or CITY in .env")
    exit()

url = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={CITY}&aqi=no"

response = requests.get(url)

if response.status_code != 200:
    print("Error:", response.text)
    exit()

data = response.json()

#Parsing 
current = data.get("current", {})
location = data.get("location", {}).get("name")
temp = current.get("temp_c")
humidity = current.get("humidity")
condition = current.get("condition", {}).get("text")

#Output 
print("\n--- Weather Report ---")
print(f"City       : {location}")
print(f"Temperature: {temp}°C")
print(f"Humidity   : {humidity}%")
print(f"Condition  : {condition}")