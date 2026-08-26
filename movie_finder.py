import requests
import re
from html import unescape


def find_event_code(movie_name):

    url = "https://in.bookmyshow.com/explore/movies-chennai"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print("Failed to get BookMyShow page")
        return None

    html = response.text

    # Extract:
    # movie URL -> event code -> movie name
    pattern = (
        r'"url":"https://in\.bookmyshow\.com/chennai/movies/'
        r'[^"]+/(ET\d+)"'
        r',"name":"([^"]+)"'
    )

    movies = re.findall(pattern, html)

    for event_code, name in movies:

        name = unescape(name)

        if name.strip().lower() == movie_name.strip().lower():

            return event_code

    return None


# -----------------------------
# TEST
# -----------------------------

MOVIE = "Insidious: Out of The Further"

event_code = find_event_code(MOVIE)

if event_code:
    print("Movie:", MOVIE)
    print("Event Code:", event_code)
else:
    print("Movie not found")