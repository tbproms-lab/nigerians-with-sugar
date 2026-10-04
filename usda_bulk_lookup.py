# usda_bulk_lookup.py
# Looks up every ingredient in your list via USDA FDC and prints
# candidate matches for each, so you can review and pick the right one.
#
# Get a free key at https://api.data.gov/signup/

import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["USDA_API_KEY"]


INGREDIENTS = [
    "plum tomato", "red bell pepper", "red onion", "scotch bonnet pepper",
    "vegetable oil", "palm oil", "bay leaves", "curry powder", "dried thyme",
    "black pepper", "tomato paste", "butter", "long grain rice",
    "black-eyed peas", "crayfish", "chicken bouillon", "mackerel",
    "egg boiled", "beef liver", "beef", "smoked paprika", "garlic",
    "melon seeds", "spinach", "yam flour", "yam", "sugar",
]

def search_food(query, page_size=3):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": query,
        "pageSize": page_size,
        "dataType": ["Foundation", "SR Legacy"],
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["foods"]

def get_carbs(food):
    for n in food.get("foodNutrients", []):
        if n.get("nutrientName") == "Carbohydrate, by difference":
            return n.get("value")
    return None

if __name__ == "__main__":
    for name in INGREDIENTS:
        print(f"\n=== {name} ===")
        try:
            foods = search_food(name)
        except requests.HTTPError as e:
            print(f"  ERROR: {e}")
            continue
        if not foods:
            print("  No matches found.")
        for food in foods:
            carbs = get_carbs(food)
            print(f"  fdcId {food['fdcId']}: {food['description']}  (carbs: {carbs}g/100g)")
        time.sleep(0.5)  # be polite to the API