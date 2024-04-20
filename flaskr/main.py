from flask import (
    Blueprint, render_template, request
)

from .tools.data_tool import *

from surprise import Reader
from surprise import KNNBasic
from surprise import Dataset
from sklearn.metrics.pairwise import cosine_similarity

bp = Blueprint('main', __name__, url_prefix='/')

games, genres, rates = loadData()


@bp.route('/', methods=('GET', 'POST'))
def index():

    # Default Genres List
    default_genres = genres.to_dict('records')
    # User Genres
    user_genres = request.cookies.get('user_genres')
    if user_genres:
        user_genres = user_genres.split(",")
    else:
        user_genres = []

    # User Rates
    user_rates = request.cookies.get('user_rates')
    if user_rates:
        user_rates = user_rates.split(",")
    else:
        user_rates = []

    # User Likes
    user_likes = request.cookies.get('user_likes')
    if user_likes:
        user_likes = user_likes.split(",")
    else:
        user_likes = []

    default_genres_games = getGamesByGenres(user_genres)
    recommendations_games, recommendations_message = getRecommendationBy(user_rates)[:12]
    likes_similar_games, likes_similar_message = getLikedSimilarBy([int(numeric_string) for numeric_string in user_likes])
    likes_games = getUserLikesBy(user_likes)

    return render_template('index.html',
                           genres=default_genres,
                           user_genres=user_genres,
                           user_rates=user_rates,
                           user_likes=user_likes,
                           default_genres_games=default_genres_games,
                           recommendations=recommendations_games,
                           recommendations_message=recommendations_message,
                           likes_similars=likes_similar_games,
                           likes_similar_message=likes_similar_message,
                           likes=likes_games,
                           )


def getUserLikesBy(user_likes):
    results = []

    if len(user_likes) > 0:
        mask = games['gameId'].isin([int(gameId) for gameId in user_likes])
        results = games.loc[mask]

        original_orders = pd.DataFrame()
        for _id in user_likes:
            game = results.loc[results['gameId'] == int(_id)]
            if len(original_orders) == 0:
                original_orders = game
            else:
                original_orders = pd.concat([game, original_orders])
        results = original_orders

    # return the result
    if len(results) > 0:
        return results.to_dict('records')
    return results


def getGamesByGenres(user_genres):
    results = []

    # ====  Do some operations ====

    if len(user_genres) > 0:
        genres_mask = genres['id'].isin([int(id) for id in user_genres])
        user_genres = [1 if has is True else 0 for has in genres_mask]
        user_genres_df = pd.DataFrame(user_genres)
        user_genres_df.index = genres['name']
        games_genres = games.iloc[:, 5:]
        mask = (games_genres.dot(user_genres_df) > 0).squeeze()
        results = games.loc[mask][:30]

    # ==== End ====

    # return the result
    if len(results) > 0:
        return results.to_dict('records')
    return results


# Modify this function
def getRecommendationBy(user_rates):
    results = []

    # ==== Do some operations ====

    # Check if there are any user_rates
    if len(user_rates) > 0:
        # Initialize a reader with rating scale from 1 to 5
        reader = Reader(rating_scale=(1, 10))

        algo = KNNBasic(sim_options={'name': 'pearson', 'user_based': True})

        # Convert user_rates to rates from the user
        user_rates = ratesFromUser(user_rates)

        # Combine rates and user_rates into training_rates
        training_rates = pd.concat([rates, user_rates], ignore_index=True)

        # Load the training data from the training_rates DataFrame
        training_data = Dataset.load_from_df(training_rates, reader=reader)

        # Build a full training set from the training data
        trainset = training_data.build_full_trainset()

        # Fit the algorithm using the trainset
        algo.fit(trainset)

        # Convert the raw user id to the inner user id using algo.trainset
        inner_id = trainset.to_inner_uid(51)

        # Get the nearest neighbors of the inner_id
        neighbors = algo.get_neighbors(inner_id, k=1)

        # Convert the inner user ids of the neighbors back to raw user ids
        neighbors_uid = [algo.trainset.to_raw_uid(x) for x in neighbors]

        # Filter out the games this neighbor likes.
        results_games = rates[rates['userId'].isin(neighbors_uid)]
        gamesIds = results_games[results_games['rating'] > 5]['gameId']

        # Convert the game ids to details.
        results = games[games['gameId'].isin(gamesIds)][:12]

    # Return the result
    if len(results) > 0:
        return results.to_dict('records'), "These games are recommended based on your ratings."
    return results, "No recommendations."
    # ==== End ====


# Modify this function
def getLikedSimilarBy(user_likes):
    results = []

    # ==== Do some operations ====
    if len(user_likes) > 0:

        # Step 1: Representing items with one-hot vectors
        item_rep_matrix, item_rep_vector, feature_list = item_representation_based_game_genres(games)

        # Step 2: Building user profile
        user_profile = build_user_profile(user_likes, item_rep_vector, feature_list)

        # Step 3: Predicting user interest in items
        results = generate_recommendation_results(user_profile, item_rep_matrix, item_rep_vector, 12)

    # Return the result
    if len(results) > 0:
        return results.to_dict('records'), "The games are similar to your liked games."
    return results, "No similar games found."

    # ==== End ====


def item_representation_based_game_genres(games_df):
    games_with_genres = games_df.copy(deep=True)

    genre_list = games_with_genres.columns[5:]
    games_genre_matrix = games_with_genres[genre_list].to_numpy()
    return games_genre_matrix, games_with_genres, genre_list


def build_user_profile(gameIds, item_rep_vector, feature_list, normalized=True):

    ## Calculate item representation matrix to represent user profiles
    user_game_rating_df = item_rep_vector[item_rep_vector['gameId'].isin(gameIds)]
    user_game_df = user_game_rating_df[feature_list].mean()
    user_profile = user_game_df.T

    if normalized:
        user_profile = user_profile / sum(user_profile.values)

    return user_profile


def generate_recommendation_results(user_profile, item_rep_matrix, games_data, k=12):
    # Convert user profile to a NumPy array
    u_v = user_profile.values
    # Convert the user profile to a 2D array
    u_v_matrix = [u_v]

    # Check for NaN values in user_profile and item_rep_matrix and handle them
    # Fill NaN values with 0 or any other appropriate value
    u_v_matrix = pd.DataFrame(u_v_matrix).fillna(0).values
    item_rep_matrix = pd.DataFrame(item_rep_matrix).fillna(0).values

    # Compute the cosine similarity
    recommendation_table = cosine_similarity(u_v_matrix, item_rep_matrix)
    
    # Create a copy of the games data
    recommendation_table_df = games_data.copy(deep=True)
    # Add the similarity scores to the data frame
    recommendation_table_df['similarity'] = recommendation_table[0]
    
    # Sort the data frame by similarity scores in descending order and take the top k results
    rec_result = recommendation_table_df.sort_values(by='similarity', ascending=False).head(k)

    # Return the top k results as a DataFrame
    return rec_result