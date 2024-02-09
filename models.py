## Recipe model
class Recipe:
    def __init__(self, recipe_id, name, short_description, nutriscore, ingredients, preparation_steps):
        self.recipe_id = recipe_id
        self.name = name
        self.short_description = short_description
        self.nutriscore = nutriscore
        self.ingredients = ingredients
        self.preparation_steps = preparation_steps
    
    @classmethod
    def from_json_data(cls, recipe_data):
        recipe_id = recipe_data["id"]
        name = recipe_data["name"]
        short_description = recipe_data["shortDescription"]
        nutriscore = recipe_data["nutriscore"]
        
        recipe_ingredients = []
        for ingredient in recipe_data["pools"][0]["cookingModes"][0]["stacks"]["ingredients"]:
            quantity = ingredient["literalQuantity"]
            product = ingredient["product"]
            ingredient_id = product["id"]
            ingredient_name = product["name"]
            recipe_ingredients.append({"name": ingredient_name, "quantity": quantity, "id": ingredient_id})

        recipe_preparation_steps = []
        for index, step in enumerate(recipe_data["pools"][0]["cookingModes"][0]["steps"]):
            step_description = step["description"]
            recipe_preparation_steps.append({"step_number": index + 1, "description": step_description})

        return cls(recipe_id, name, short_description, nutriscore, recipe_ingredients, recipe_preparation_steps)
    
    def __str__(self):
        ingredients_str = "\n".join([f"Name: {ingredient['name']}, Quantity: {ingredient['quantity']}, ID: {ingredient['id']}" for ingredient in self.ingredients])
        preparation_steps_str = "\n".join([f"Step {step['step_number']}: {step['description']}" for step in self.preparation_steps])
        return f"Recipe ID: {self.recipe_id}\nName: {self.name}\nShort Description: {self.short_description}\nNutriscore: {self.nutriscore}\nIngredients:\n{ingredients_str}\nPreparation Steps:\n{preparation_steps_str}"