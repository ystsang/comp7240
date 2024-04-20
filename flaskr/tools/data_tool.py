import os
import pandas as pd

def loadData():
    return getGames(), getGenre(), getRates()

# Function to load board games data from 'game.csv'
def getGames():
    # Get the root path
    rootPath = os.path.abspath(os.getcwd())
    path = f"{rootPath}/flaskr/static/bg_data/games.csv"
    
    # Define the columns to be selected
    selected_columns = [
        'BGGId', 'Name', 'YearPublished', 'Description', 'ImagePath',
        'Cat:Thematic', 'Cat:Strategy', 'Cat:War', 'Cat:Family',
        'Cat:CGS', 'Cat:Abstract', 'Cat:Party', 'Cat:Childrens'
    ]
    
    # Read the CSV file and process data
    df = pd.read_csv(path, delimiter=",")
    
    # Filter the DataFrame to include only the specified columns
    df = df[selected_columns]
    
    # Define a dictionary for renaming columns
    rename_dict = {
        'BGGId': 'gameId',
        'Name': 'title',
        'YearPublished': 'year',
        'Description': 'overview',
        'ImagePath': 'cover_url'
    }
    
    # Add renaming for category columns to remove the "Cat:" prefix
    rename_dict.update({col: col.replace('Cat:', '') for col in selected_columns if 'Cat:' in col})
    
    # Rename columns in the DataFrame
    df.rename(columns=rename_dict, inplace=True)
    
    # Limit to the first 5000 rows (or other desired number)
    #df = df.head(5000)

    return df

# Function to load categories (equivalent to genres) from the CSV file
def getGenre():
    rootPath = os.path.abspath(os.getcwd())
    path = f"{rootPath}/flaskr/static/bg_data/games.csv"  # Using 'game.csv' file to load categories
    df = pd.read_csv(path, delimiter=",")
    
    # Extracting category columns from the game CSV
    # Example: Cat:Thematic, Cat:Strategy, Cat:War, etc.
    category_columns = [col for col in df.columns if col.startswith('Cat:')]
    
    # Preparing a dictionary of categories with their names and IDs
    categories_dict = {i + 1: col.split(":")[1] for i, col in enumerate(category_columns)}
    
    # Convert dictionary to DataFrame
    df = pd.DataFrame(list(categories_dict.items()), columns=["id", "name"])
    
    # Reorder the DataFrame columns so that "name" is the first column and "id" is the second column
    df = df[["name", "id"]]
    
    return df

# Function to load user ratings from 'user_rating.csv'
def getRates():
    rootPath = os.path.abspath(os.getcwd())
    path = f"{rootPath}/flaskr/static/bg_data/user_ratings.csv"

    # Read the CSV file and set the column names as specified
    df = pd.read_csv(path, delimiter=",", names=["BGGId", "Rating", "Username"], low_memory=False)
    
    # Reorder the columns so that they are in the order 'Username', 'BGGId', 'Rating'
    df = df[['Username', 'BGGId', 'Rating']]
    
    # Rename the columns as desired
    df = df.rename(columns={
        "Username": "userId",
        "BGGId": "gameId",
        "Rating": "rating"
    })
        
    # Drop the first row from the DataFrame if it's header or unnecessary data
    df = df.drop(index=0)
    
    # Change the data types of the columns
    df = df.astype({
        "userId": str,   # Convert 'userId' column to string
        "gameId": int,  # Convert 'gameId' column to integer
        "rating": float  # Convert 'rating' column to float
    })
    
    # Generate a mapping of unique usernames to userIds
    user_mapping = {user: str(i + 1) for i, user in enumerate(df['userId'].unique())}
    
    # Map usernames to userIds
    df['userId'] = df['userId'].map(user_mapping)
    
    # Sort DataFrame based on userId column
    df = df.sort_values(by='userId')
    
    # Limit the DataFrame to the first 1,000 rows
    #df = df.head(1000)
    # Limit the DataFrame to first 50 users (11027 rows)
    df = df[df['userId'].astype(int) <= 50]
    
    return df

# Function to create a DataFrame of user ratings from raw data
def ratesFromUser(rates):
    itemID = []
    userID = []
    rating = []
    
    # Parse the rates provided as a list of strings
    for rate in rates:
        items = rate.split("|")
        userID.append(int(items[0]))
        itemID.append(int(items[1]))
        rating.append(int(items[2]))
    
    # Create a dictionary of the parsed data
    ratings_dict = {
        "userId": userID,
        "gameId": itemID,
        "rating": rating,
    }

    # Return a DataFrame created from the dictionary
    return pd.DataFrame(ratings_dict)