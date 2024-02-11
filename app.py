import re
import streamlit as st
import pandas as pd
from collections import Counter
import plotly.express as px

@st.cache_data
def load_data():
    df_recipes = pd.read_csv('recipes.csv')
    df_recipes = df_recipes.drop_duplicates(subset='recipe_id', keep='first')
    df_recipes['recipe_id'] = pd.to_numeric(df_recipes['recipe_id'], errors='coerce')
    df_recipes.dropna(subset=['recipe_id'], inplace=True)
    df_recipes = parsed_ingredients_data(df_recipes=df_recipes)
    df_recipes['num_ingredients'] = df_recipes['parsed_ingredients'].apply(lambda x: len([ingredient for ingredient in x if ingredient]))
    return df_recipes

def remove_text_inside_parentheses(text):
    return re.sub(r'\([^)]*\)', '', text)

def parsed_ingredients_data(df_recipes):
    df_recipes['parsed_ingredients'] = pd.Series(dtype='object')
    for index, row in df_recipes.iterrows():
        ingredients_list = row['recipe_ingredients'].split('\n')
        cleaned_ingredient_names = set()
        for ingredient in ingredients_list:
            # Remove text inside parentheses
            ingredient = remove_text_inside_parentheses(ingredient)
            # Remove text after "-" and ":" then split by ',' and take the first part
            ingredient_name = ingredient.split('-')[0].split(':')[0].split(',')[0].lower().strip()
            cleaned_ingredient_names.add(ingredient_name)
        df_recipes.at[index, 'parsed_ingredients'] = cleaned_ingredient_names
    return df_recipes

@st.cache_data
def plot_ingredients_repartitions(st, df_recipes, nbr_of_most_used_ingredients: int = 25):
    all_ingredients = []

    for index, row in df_recipes.iterrows():
        for ingredient in row["parsed_ingredients"]:
            ingredient_name = ingredient.split(',')[0]
            all_ingredients.append(ingredient_name)

    ingredient_counts = Counter(all_ingredients)
    ingredient_df = pd.DataFrame.from_dict(ingredient_counts, orient='index', columns=['frequency'])
    ingredient_df = ingredient_df.sort_values(by='frequency', ascending=False)

    most_used_ingredients = ingredient_df.head(nbr_of_most_used_ingredients)
    fig = px.bar(
        most_used_ingredients, 
        x=most_used_ingredients.index, 
        y='frequency',
        title=f'Les {nbr_of_most_used_ingredients} ingrédients les plus utilisés',
        labels={'x': 'Ingredient', 'frequency': 'Frequency'
    })
    fig.update_layout(xaxis_tickangle=-45, xaxis_title='Ingredient', yaxis_title='Frequency', plot_bgcolor='white')
    st.plotly_chart(fig)

def find_similar_recipes(central_recipe_id, df_recipes):
    central_ingredients = df_recipes.loc[df_recipes['recipe_id'] == central_recipe_id, 'parsed_ingredients'].iloc[0]
    df_recipes['shared_ingredients_count'] = df_recipes.apply(lambda row: calculate_shared_ingredients(row['parsed_ingredients'], central_ingredients) if row['recipe_id'] != central_recipe_id else 0, axis=1)
    # Sort the DataFrame based on 'shared_ingredients_count' to find the most similar recipes
    similar_recipes = df_recipes[df_recipes['recipe_id'] != central_recipe_id].sort_values(by='shared_ingredients_count', ascending=False)
    return similar_recipes

def contains_keywords(ingredients_set, keywords):
    keywords = [keyword.lower() for keyword in keywords]
    return any(keyword in ingredient for ingredient in ingredients_set for keyword in keywords)

## Calculate the number of shared ingredients
def calculate_shared_ingredients(ingredients_set, central_ingredients):
    return len(ingredients_set.intersection(central_ingredients))

def main():
    st.set_page_config(page_title="Master Chief", page_icon="👨‍🍳", layout="wide", initial_sidebar_state="auto")
    st.image("logo.png", width=150)
    st.title('Des recettes simples et savoureuses à la portée de tous! 😋')
    bmc_link = "https://www.buymeacoffee.com/pownedj"
    st.markdown(f"[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)]({bmc_link})", unsafe_allow_html=True)
    st.markdown("""
    Explorez notre collection de recettes et découvrez des plats délicieux à préparer.  
    Que vous cherchiez des **recettes rapides à réaliser en moins de 30 minutes** ou des **idées pour intégrer des ingrédients spécifiques** à votre cuisine, 
    notre guide est là pour vous inspirer.  
    Trouvez votre prochain coup de cœur culinaire dès aujourd'hui !
    """)
    st.markdown("---")

    df_recipes = load_data()

    # Filter recipes based on input
    st.markdown(f"## Trouver des recettes utilisant certains ingrédients:")
    ingredient_search_term = st.text_input('Entrez un ingrédient (par exemple, poulet) pour trouver des recettes correspondantes:', 'poulet')
    filtered_recipes = df_recipes[df_recipes['parsed_ingredients'].apply(lambda ingredients: any(ingredient_search_term.lower() in ingredient for ingredient in ingredients))]
    if not filtered_recipes.empty:
        st.markdown(f"## Recettes contenant '{ingredient_search_term}':")
        st.dataframe(filtered_recipes[['recipe_id', 'recipe_name', 'parsed_ingredients']])
    else:
        st.markdown(f"### Aucune recette trouvée contenant '{ingredient_search_term}'.")
    
    # Show ingredients distribution graph
    st.markdown("---")
    st.markdown(f"## Répartitions des ingrédients les plus utilisés dans les recettes:")
    num_most_used_ingredients = st.number_input('Nombre d’ingrédients les plus utilisés à afficher', min_value=1, value=20, step=1)
    plot_ingredients_repartitions(st=st, df_recipes=df_recipes, nbr_of_most_used_ingredients=num_most_used_ingredients)
    st.markdown("---")

    ## Find the X recipes with the least amount of ingredients
    st.markdown(f"## Filtrer les recettes sur le nombre d'ingrédients utilisés:")
    num_recipes = st.slider('Nombre de recettes à afficher', min_value=1, max_value=20, value=5)
    sorted_recipes = df_recipes.sort_values(by='num_ingredients', ascending=True)
    sorted_recipes_by_number_of_ingredients = sorted_recipes.iloc[:num_recipes]
    st.dataframe(sorted_recipes_by_number_of_ingredients)
    st.markdown("---")

    ## Filter Fish/Meat recipes
    fish_keywords = ['poisson', 'saumon', 'merlu', 'cabillaud', 'truite', 'thon', 'bar', 'maquereau', 'dorade', 'sole', 'églefin', 'sardine', 'morue', 'turbot', 'lieu']
    meat_keywords = ['viande', 'poulet', 'boeuf', 'volaille', 'steak', 'entrecôte', 'porc', 'cochon', 'dinde', 'saucisse', 'lapin']
    df_recipes['contains_fish'] = df_recipes['parsed_ingredients'].apply(lambda x: contains_keywords(x, fish_keywords))
    df_recipes['contains_meat'] = df_recipes['parsed_ingredients'].apply(lambda x: contains_keywords(x, meat_keywords))
    ## TODO: How to show fish/meat recipes in a nice manner
    st.markdown("---")


    ## Find similar recipes from a "Central" recipe
    st.markdown(f"## Trouver des recettes similaires:")
    #similar_recipes = find_similar_recipes(central_recipe_id=1247, df_recipes=df_recipes)
    #st.dataframe(similar_recipes[['recipe_id', 'recipe_name', 'parsed_ingredients', 'shared_ingredients_count']].head())
    st.markdown("---")

    # Show dataset
    if st.button("Afficher le Dataset"):
        columns_to_display = ['recipe_id', 'recipe_name', 'parsed_ingredients']
        st.dataframe(df_recipes[columns_to_display])

if __name__ == "__main__":
    main()