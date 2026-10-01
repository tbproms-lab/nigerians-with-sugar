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
