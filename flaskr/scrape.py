from .tools.scrape_tool import *

from flask import (
    Blueprint, current_app
)

bp = Blueprint('scrape', __name__, url_prefix='/scrape')


# This function aims to re-scrape the cover of the games. Do not run it without supervisor!!.
@bp.route('/', methods=('GET', 'POST'))
def index():
    games = getOriginalItems()

    totalNum = len(games)
    current = 0

    file = open(f"{current_app.root_path}/static/ml_data_lab2/game_info_new.csv", "a")
    titles = games[0]
    genres = titles.pop(2)
    titles.append("cover_url")
    titles.append(genres)
    file.write(','.join(titles) + "\n")
    file.close()

    for game in games[1:]:
        print(f"{(current / totalNum) * 100 : .2f} %")
        image_url = get_game_png(game[1])
        print(image_url)
        genres = game.pop(2)
        if image_url is not None:
            game.append(image_url)
        else:
            game.append("")
        game.append(genres)
        file = open(f"{current_app.root_path}/static/ml_data_lab2/game_info_new.csv", "a")
        file.write(','.join(game) + "\n")
        file.close()
        current += 1

    file.close()

    return "Complete!"



