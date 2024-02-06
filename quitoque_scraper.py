import requests, json
from bs4 import BeautifulSoup

## GET JSON FROM operationName getFilterRecipes Request (use Network dev tool within browser)
## PARSE JSON FILES TO KEEP ONLY RECIPES (RECEIPE ID)
## Network call to grab recipe details (ingredients & preparation steps)

JSON_RECEIPES_FILE_PATH = "recipes1.json"
MAX_COOKING_TIME = 30

def parse_recipes_json_file(file_name) -> list:
    with open(file_name, 'r', encoding='utf-8') as file:
        data = json.load(file)

    recipes = data["data"]["filterRecipes"]["recipes"]
    recipe_ids = []
    for recipe in recipes:
        for pool in recipe['pools']:
            if pool['nbPerson'] == 2:
                if cooking_time := pool["cookingModes"][0]["cookingTime"] <= MAX_COOKING_TIME:
                    recipe_ids.append(recipe['id'])
    return recipe_ids

## Example recipe_id: "12599"
def get_recipe_details_from_api_call(recipe_id: str):
    endpoint_url = f"https://mgs.quitoque.fr/graphql?operationName=getRecipe&variables=%7B%22id%22%3A%22{recipe_id}%22%2C%22date%22%3Anull%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%2204af4d1a48fd536a67292733e23a2afcf6d0da9770ab07055c59b754eec9bd6d%22%7D%7D"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}

    response = requests.get(endpoint_url, headers=headers)
    json_data = response.json()
    
    recipe_data = json_data["data"]["recipe"]
    short_description = recipe_data["shortDescription"]
    nutriscore = recipe_data["nutriscore"]
    print(f"DESCRITPION: {short_description}")
    print(f"NURISCORE: {nutriscore}")
    
    recipe_details = recipe_data["pools"][0]["cookingModes"][0]

    recipe_ingredients = recipe_data["pools"][0]["cookingModes"][0]["stacks"]["ingredients"]
    for ingredient in recipe_ingredients:
        quantity = ingredient["literalQuantity"]
        product = ingredient["product"]
        ingredient_id = product["id"]
        ingredient_name = product["name"]
        print(f"INGREDIENT: name: {ingredient_name} - name: {ingredient_name} - quantity: {quantity} - id: {ingredient_id}")

    recipe_preparation_steps = recipe_details["steps"]
    for index, step in enumerate(recipe_preparation_steps):
        step_description = step["description"]
        print(f"\nSTEP {index}: {step_description}")

def main():
    recipe_ids = parse_recipes_json_file(JSON_RECEIPES_FILE_PATH)

    for recipe_id in recipe_ids:
        ## TODO: Call get_recipe_details_from_api_call()
        print(recipe_id)

main()

get_recipe_details_from_api_call(recipe_id="12122")

## TODO: STORE EVERY RECIPE !
## Create DB model: recipe_id, name, description, nutriscore, ingredients, steps