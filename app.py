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
    df_recipes['recipe_id'] = pd.to_numeric(df_recipes['recipe_id'], errors='coerce').astype(int)
    df_recipes = parsed_ingredients_data(df=df_recipes)
    df_recipes['num_ingredients'] = df_recipes['parsed_ingredients'].apply(lambda x: len([ingredient for ingredient in x if ingredient]))
    fish_keywords = ['poisson', 'saumon', 'merlu', 'cabillaud', 'truite', 'thon', 'bar', 'maquereau', 'dorade', 'sole', 'églefin', 'sardine', 'morue', 'turbot', 'lieu']
    meat_keywords = ['viande', 'poulet', 'boeuf', 'volaille', 'steak', 'entrecôte', 'porc', 'cochon', 'dinde', 'saucisse', 'lapin']
    df_recipes['contains_fish'] = df_recipes['parsed_ingredients'].apply(lambda x: contains_keywords(x, fish_keywords))
    df_recipes['contains_meat'] = df_recipes['parsed_ingredients'].apply(lambda x: contains_keywords(x, meat_keywords))
    return df_recipes

def remove_text_inside_parentheses(text):
    return re.sub(r'\([^)]*\)', '', text)

def parsed_ingredients_data(df):
    df['parsed_ingredients'] = pd.Series(dtype='object')
    for index, row in df.iterrows():
        ingredients_list = row['recipe_ingredients'].split('\n')
        cleaned_ingredient_names = set()
        for ingredient in ingredients_list:
            ingredient = remove_text_inside_parentheses(ingredient)
            ingredient_name = ingredient.split('-')[0].split(':')[0].split(',')[0].lower().strip()
            cleaned_ingredient_names.add(ingredient_name)
        df.at[index, 'parsed_ingredients'] = cleaned_ingredient_names
    return df

def filter_recipes_ingredients(st, df):
    unique_ingredients = sorted(set([ingredient for sublist in df['parsed_ingredients'].tolist() for ingredient in sublist]))
    selected_ingredients = st.multiselect('Sélectionnez les ingrédients:', unique_ingredients)
    filtered_recipes = df[df['parsed_ingredients'].apply(lambda ingredients: all(item in ingredients for item in selected_ingredients))]

    if not filtered_recipes.empty and selected_ingredients:
        st.dataframe(filtered_recipes[['recipe_id', 'recipe_name', 'parsed_ingredients', 'num_ingredients']], use_container_width=True)
    elif filtered_recipes.empty and not selected_ingredients:
        st.markdown(f"### Aucune recette trouvée contenant les ingrédients: '{selected_ingredients}'.")
    else:
        st.markdown(f"Veuillez sélectionner des ingrédients pour afficher les recettes correspondantes")

@st.cache_data
def plot_ingredients_repartitions(st, df, nbr_of_most_used_ingredients: int = 25):
    all_ingredients = []

    for index, row in df.iterrows():
        for ingredient in row["parsed_ingredients"]:
            ingredient_name = ingredient.split(',')[0]
            all_ingredients.append(ingredient_name)

    ingredient_counts = Counter(all_ingredients)
    ingredient_df = pd.DataFrame.from_dict(ingredient_counts, orient='index', columns=['frequency'])
    ingredient_df = ingredient_df.sort_values(by='frequency', ascending=False)
    most_used_ingredients = ingredient_df.head(nbr_of_most_used_ingredients)
    fig = px.bar(most_used_ingredients, x=most_used_ingredients.index,  y='frequency', labels={'x': 'Ingredient', 'frequency': 'Frequency'})
    fig.update_layout(xaxis_tickangle=-45, xaxis_title='Ingredient', yaxis_title='Frequency', plot_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)

def contains_keywords(ingredients_set, keywords):
    keywords = [keyword.lower() for keyword in keywords]
    return any(keyword in ingredient for ingredient in ingredients_set for keyword in keywords)

def calculate_shared_ingredients(ingredients_set, central_ingredients):
    return len(ingredients_set.intersection(central_ingredients))

def display_fish_meat_distributions(st, df):
    fish_recipes_count = df['contains_fish'].sum()
    meat_recipes_count = df['contains_meat'].sum()
    labels = ['Recettes de poisson', 'Recettes de viande']
    values = [fish_recipes_count, meat_recipes_count]
    fig = px.pie(names=labels, values=values)
    st.plotly_chart(fig, use_container_width=True)

def random_recipe_for_category(st, df, category):
    if st.button('Afficher une recette aléatoire'):
        if category == 'Poisson':
            filtered_recipes = df[df['contains_fish']]
        else:
            filtered_recipes = df[df['contains_meat']]

        if not filtered_recipes.empty:
            random_recipe = filtered_recipes.sample()
            st.markdown(f"### {random_recipe.iloc[0]['recipe_name']}")
            st.markdown(f"**Id :** {random_recipe.iloc[0]['recipe_id']}")
            ingredients_string = ", ".join(random_recipe.iloc[0]['parsed_ingredients'])
            st.markdown(f"**Ingrédients :** {ingredients_string}")
        else:
            st.write("Aucune recette trouvée dans cette catégorie.")

def calculate_shared_ingredients(ingredients_list, central_ingredients):
    return len(set(ingredients_list) & set(central_ingredients))

def find_similar_recipes(df, central_recipe_id, min_shared_ingredients):
    central_ingredients = df.loc[df['recipe_id'] == central_recipe_id, 'parsed_ingredients'].iloc[0]
    df['shared_ingredients_count'] = df.apply(lambda row: calculate_shared_ingredients(row['parsed_ingredients'], central_ingredients) if row['recipe_id'] != central_recipe_id else 0, axis=1)
    similar_recipes = df[(df['recipe_id'] != central_recipe_id) & (df['shared_ingredients_count'] >= min_shared_ingredients)].sort_values(by='shared_ingredients_count', ascending=False)
    return similar_recipes

def main():
    st.set_page_config(page_title="Master Chef", page_icon="👨‍🍳", layout="wide", initial_sidebar_state="auto")
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

    # Filter recipes based on selected ingredients
    st.markdown(f"## Trouver des recettes utilisant certains ingrédients")
    filter_recipes_ingredients(st=st, df=df_recipes)
    
    # Show ingredients distribution graph
    st.markdown("---")
    st.markdown(f"## Répartitions des ingrédients les plus utilisés dans les recettes")
    num_most_used_ingredients = st.number_input('Nombre d’ingrédients les plus utilisés à afficher', min_value=1, value=20, step=1)
    plot_ingredients_repartitions(st=st, df=df_recipes, nbr_of_most_used_ingredients=num_most_used_ingredients)
    st.markdown("---")

    ## Find the X recipes with the least amount of ingredients
    st.markdown(f"## Recettes utilisant le moins d'ingrédients")
    num_recipes = st.slider('Nombre de recettes à afficher', min_value=1, max_value=30, value=5)
    sorted_recipes = df_recipes.sort_values(by='num_ingredients', ascending=True)
    sorted_recipes_by_number_of_ingredients = sorted_recipes.iloc[:num_recipes]
    columns_to_display = ['recipe_id', 'recipe_name', 'parsed_ingredients', 'num_ingredients']
    st.dataframe(sorted_recipes_by_number_of_ingredients[columns_to_display], use_container_width=True)
    st.markdown("---")

    ## Display Fish/Meat recipes
    st.markdown(f"## Répartitions des recettes intégrant de la viande et du poisson")
    display_fish_meat_distributions(st=st, df=df_recipes)
    st.markdown("---")

    ## Show random Recipe
    st.markdown(f"## Choisir une recette")
    recipe_category = st.selectbox('Choisissez une catégorie de recette :', ['Poisson', 'Viande'])
    random_recipe_for_category(st=st, df=df_recipes, category=recipe_category)
    st.markdown("---")

    ## Find similar recipes from a "Central" recipe
    st.markdown(f"## Trouver des recettes similaires")
    recipe_options = df_recipes.apply(lambda x: f"{x['recipe_id']} - {x['recipe_name']}", axis=1).tolist()
    selected_recipe = st.selectbox('Sélectionnez l\'ID de la recette de départ :', recipe_options)
    central_recipe_id = int(selected_recipe.split(' - ')[0])
    min_shared_ingredients = st.number_input('Nombre minimum d\'ingrédients en commun :', min_value=1, value=1, step=1)

    if st.button('Trouver des recettes similaires'):
        central_recipe = df_recipes[df_recipes['recipe_id'] == central_recipe_id]
        st.dataframe(central_recipe[['recipe_id', 'recipe_name', 'parsed_ingredients', 'num_ingredients']], use_container_width=True)
        similar_recipes = find_similar_recipes(df_recipes, central_recipe_id, min_shared_ingredients)
        if not similar_recipes.empty:
            st.dataframe(similar_recipes[['recipe_id', 'recipe_name', 'parsed_ingredients', 'num_ingredients']], use_container_width=True)
        else:
            st.write("Aucune recette similaire trouvée.")
    st.markdown("---")

    # Show dataset
    if st.button("Afficher toutes les recettes"):
        columns_to_display = ['recipe_id', 'recipe_name', 'parsed_ingredients', 'num_ingredients']
        st.dataframe(df_recipes[columns_to_display], use_container_width=True)
    
    ## TODO:
    # - Link to quitoque (recipe_id)
    # - Create liste de courses

if __name__ == "__main__":
    main()