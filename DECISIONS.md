I decided to go with a many to many join table for establishing the connections between dishes and the ingredients because one ingredient can belong to many dishes and one dish can have many ingredients. This way, we're building meals that can co-exist in the same universe with the same ingredients.

Glycemic load is calculated on each run of dish as this avoids a static GL if perhaps a user were to swap an ingredient to replace another in a dish, the GL will update and reload based on this new information

Swap_ingredient will reference dish ingredients, because swapping an ingredient in a dish only makes sense in the context of that singular dish. It will need to access ingredients as well in order to replace it in the dish ingredients.

User_preferences shouldn't be JSONB since it's a fixed tag set, the same tags on the dishses (sweet, spicy, vegan, vegetarian)- same many-to-many shape as ingredients. It need a tags table + join tables for both users and dishes.

Made a few decisisons (and questions) while creating the schema today 9/27/26:

- `taste_preferences` became `tags` plus join tables, because it's a fixed set of values, not open-ended data
- `swaps` points at a `dish_ingredients` row (composite foreign key) so a swap can only exist for an ingredient the dish actually uses
- `swaps.swap_ingredient_id` has no `ON DELETE CASCADE`, so deleting an ingredient that's a suggested replacement is blocked instead of silently erasing swap advice
- Eating out vs. cooking at home is a user or request setting, not a column on `swaps`. Open question: what data powers eating-out mode?
- GL is computed on read, not stored
- Open problem: converting units like "cup" into grams so GL can be calculated

Verified the composite foreign key on swaps by testing an invalid insert — Postgres rejected (moi moi, white rice) since that pair doesn't exist in dish_ingredients. Confirms the constraint, not application code, enforces that swaps only apply to ingredients a dish actually uses.

NOTE FOR FUTURE: user-facing add/remove ingredient is a request-time GL calculation, not a dish edit — doesn't need new tables yet.

General Overview of Decisions made till 10/4/2026

Schema shape

Many-to-many ingredients-to-recipes needs a join table (dish_ingredients), not a JSON blob — the database can then enforce the relationship itself.
taste_preferences on Users started as JSONB, but was corrected to a proper tags table plus two join tables (user_tag_preferences, dish_tags), since it's a fixed set of values, not open-ended data — same many-to-many pattern as ingredients.
GL (glycemic load) is computed on read, not stored, since a swap can change a dish's ingredients and a cached value would go stale.
GI (glycemic index) lives on ingredients, since it's a fixed property of the food; quantity lives on the join table, since that's where "how much" belongs.

The swaps table

A swap applies to a specific dish's use of an ingredient, not an ingredient in general — so swaps points at a dish_ingredients row via a composite foreign key, not two separate foreign keys to dishes and ingredients.
Verified this actually works by testing an invalid insert — Postgres rejected a swap for an ingredient a dish doesn't use, confirming the constraint enforces it, not application code.
swap_ingredient_id has no ON DELETE CASCADE — deleting an ingredient that's a suggested replacement is blocked, not silently erased.
Cooking vs. eating-out mode is not a column on swaps — it's a per-request or per-user setting, since it describes the situation, not the swap itself. Open question, still unresolved: what data actually powers eating-out guidance (portions/pairings), since it isn't ingredient substitution.

Nullability / messy real-world data

quantity on dish_ingredients is nullable, to allow "a pinch" or "to taste" without inventing a fake number.
ingredients.gi and ingredients.carbs are both nullable now (changed from NOT NULL) — the priority is having the ingredient present at all; nutrition numbers get filled in later, per-ingredient, as real sourced data becomes available. name is the only required column.

Data sourcing

Real GI/nutrition data only — no AI-aggregated or guessed values get used in seed.sql. Two sources: USDA FDC (API, for carbs/macros) and a GI chart (manual lookup, since scraping it hit bot-protection/JS issues not worth debugging under deadline pressure).
Where recipes gave ranges or vague choices ("meat of your choice"), pick one concrete option and note the choice, rather than storing ambiguity.
The USDA match-picking is a one-time, permanent decision per ingredient — once confirmed and written to the source column (with the exact fdcId), the app never calls the API again for that ingredient.
The ingredient list is meant to grow over time, not be front-loaded complete — new dishes add new ingredient rows with NULL nutrition data, and lookup scripts query WHERE carbs IS NULL to find what still needs research.

Product scope

Add/remove-ingredient ("what if I skip this") is a request-time GL calculation, not an edit to a dish's real recipe — no new table needed yet.
Stock was simplified to water in the jollof recipe, to avoid treating a recipe-as-ingredient.
