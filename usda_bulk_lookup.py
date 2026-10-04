# usda_bulk_lookup.py
# Queries YOUR database for ingredients missing carbs data,
# looks each one up in USDA, re-ranks results to favor plain
# whole foods over snacks/processed items, and writes back
# the full nutrient profile you confirm.

import os
import re
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["USDA_API_KEY"]
DB_NAME = "nigerian_meals"

NUTRIENT_MAP = {
    "Carbohydrate, by difference": "carbs",
    "Energy": "calories",
    "Protein": "protein",
    "Total lipid (fat)": "fat",
    "Fiber, total dietary": "fiber",
    "Sugars, Total": "sugar",
    "Sodium, Na": "sodium",
    "Cholesterol": "cholesterol",
}

# Words that suggest a processed/snack match rather than a plain whole food.
JUNK_WORDS = [
    "snack", "babyfood", "cookie", "cake", "cracker", "chip", "soup",
    "candy", "pie", "croissant", "strudel", "bologna", "sausage",
    "restaurant", "fast foods", "frozen", "canned", "cereal",
]

def get_missing_ingredients():
    conn = psycopg2.connect(dbname=DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM ingredients WHERE carbs IS NULL ORDER BY name;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def clean_query(name):
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", name)
    return re.sub(r"\s+", " ", cleaned).strip()

def search_food(query, page_size=25):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": API_KEY,
        "query": clean_query(query),
        "pageSize": page_size,
        "dataType": ["Foundation", "SR Legacy"],
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["foods"]

def rank_score(description):
    desc_lower = description.lower()
    score = 0
    if "raw" in desc_lower:
        score -= 10
    for word in JUNK_WORDS:
        if word in desc_lower:
            score += 10
    score += len(description) * 0.1  # slight preference for shorter/simpler names
    return score

def get_nutrients(food):
    values = {col: None for col in NUTRIENT_MAP.values()}
    for n in food.get("foodNutrients", []):
        name = n.get("nutrientName")
        if name in NUTRIENT_MAP:
            values[NUTRIENT_MAP[name]] = n.get("value")
    return values

def update_ingredient(ingredient_id, nutrients, source):
    conn = psycopg2.connect(dbname=DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """UPDATE ingredients
           SET carbs = %s, calories = %s, protein = %s, fat = %s,
               fiber = %s, sugar = %s, sodium = %s, cholesterol = %s,
               source = source || %s
           WHERE id = %s;""",
        (nutrients["carbs"], nutrients["calories"], nutrients["protein"], nutrients["fat"],
         nutrients["fiber"], nutrients["sugar"], nutrients["sodium"], nutrients["cholesterol"],
         f" | USDA: {source}", ingredient_id),
    )
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    ingredients = get_missing_ingredients()
    print(f"{len(ingredients)} ingredients still need data.\n")

    for ing_id, name in ingredients:
        print(f"\n=== {name} (id {ing_id}) ===")
        try:
            foods = search_food(name)
        except requests.HTTPError as e:
            print(f"  ERROR: {e}")
            continue
        if not foods:
            print("  No matches found. Skipping.")
            continue

        foods_sorted = sorted(foods, key=lambda f: rank_score(f["description"]))[:10]

        for i, food in enumerate(foods_sorted):
            n = get_nutrients(food)
            print(f"  [{i}] {food['description']}  (carbs: {n['carbs']}g/100g, protein: {n['protein']}g, fat: {n['fat']}g)")
        choice = input("  Pick a number to save, or press Enter to skip: ").strip()
        if choice.isdigit() and int(choice) < len(foods_sorted):
            food = foods_sorted[int(choice)]
            n = get_nutrients(food)
            update_ingredient(ing_id, n, food["description"])
            print(f"  Saved: {n}")