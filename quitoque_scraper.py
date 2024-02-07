import requests, json, csv, time
from bs4 import BeautifulSoup
from typing import List
from models import Recipe

MAX_COOKING_TIME = 30
OUTPUT_CSV_FILE_NAME = "recipes.csv"

def get_recipes_ids(page_number: int) -> List[str]:
    endpoint_url = f"https://mgs.quitoque.fr/graphql?operationName=getFilterRecipes&variables=%7B%22page%22%3A{page_number}%2C%22filter%22%3A%7B%22name%22%3A%22%22%2C%22facets%22%3A%5B%5D%7D%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%221763069ea168727f095193101384d9000684552be5f6e67b3e0c41921f188309%22%7D%7D"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}
    response = requests.get(endpoint_url, headers=headers)
    json_data = response.json()

    recipes = json_data["data"]["filterRecipes"]["recipes"]

    recipe_ids = []
    for recipe in recipes:
        for pool in recipe['pools']:
            if pool['nbPerson'] == 2:
                if cooking_time := pool["cookingModes"][0]["cookingTime"] <= MAX_COOKING_TIME:
                    recipe_ids.append(recipe['id'])
    return recipe_ids

## Example recipe_id: "12599"
def get_recipe_details(recipe_id: str) -> Recipe:
    endpoint_url = f"https://mgs.quitoque.fr/graphql?operationName=getRecipe&variables=%7B%22id%22%3A%22{recipe_id}%22%2C%22date%22%3Anull%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%2204af4d1a48fd536a67292733e23a2afcf6d0da9770ab07055c59b754eec9bd6d%22%7D%7D"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}

    ## TODO: try/catch
    response = requests.get(endpoint_url, headers=headers)
    json_data = response.json()
    recipe_data = json_data["data"]["recipe"]
    return Recipe.from_json_data(recipe_data)

def write_to_csv(recipes: List[Recipe]):
    fieldnames = ['recipe_id', 'recipe_name', 'recipe_description', 'recipe_nutriscore', 'recipe_ingredients', 'recipe_reproduction_steps']
    with open(OUTPUT_CSV_FILE_NAME, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for recipe in recipes:
            ingredients_str = "\n".join([f"{ingredient['name']}, {ingredient['quantity']}, {ingredient['id']}" for ingredient in recipe.ingredients])
            preparation_steps_str = "\n".join([f"Step {step['step_number']}: {step['description']}" for step in recipe.preparation_steps])

            writer.writerow({
                'recipe_id': recipe.recipe_id,
                'recipe_name': recipe.name,
                'recipe_description': recipe.short_description,
                'recipe_nutriscore': recipe.nutriscore,
                'recipe_ingredients': ingredients_str, 
                'recipe_reproduction_steps': preparation_steps_str
            })

def main():
    recipe_ids = get_recipes_ids(page_number=0)
    unique_recipe_ids = list(set(recipe_ids))
    print(f"Fetched unique recipes_ids: {unique_recipe_ids}")

    recipes_details = []
    for recipe_id in unique_recipe_ids:
        time.sleep(8)
        print(f"Will fetch recipe details with id: {recipe_id}")
        recipe_details = get_recipe_details(recipe_id)
        recipes_details.append(recipe_details)

    print("Will write recipes to CSV file")
    write_to_csv(recipes_details)
    print("Recipes succesfuly stored in CSV file")

main()