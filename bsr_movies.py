import requests
import re
from html import unescape

date = "20260827"

url = (
    f"https://in.bookmyshow.com/cinemas/chennai/"
    f"cinepolis-bsr-mall-omr-thoraipakkam/"
    f"buytickets/CBMC/{date}"
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers)

print("Status:", response.status_code)

html = response.text


# --------------------------------------------------
# Find each movie block
# --------------------------------------------------

pattern = re.compile(
    r'<a href="/movies/chennai/[^"]+/(ET\d+)"'
    r'[^>]*>(.*?)</a>'
    r'.*?'
    r'<a href="/explore/movies\?languages=([^"]+)"'
    r'[^>]*>(.*?)</a>'
    r'.*?'
    r'<span[^>]*>([^<]+)</span>'
    r'.*?'
    r'aria-label="Book ([^"]+)"',
    re.DOTALL
)

matches = pattern.findall(html)


print("\n===== MOVIES AT CINEPOLIS BSR =====\n")


for i, match in enumerate(matches, start=1):

    event_code = match[0]

    movie_name = re.sub(
        r"<.*?>",
        "",
        match[1]
    )

    movie_name = unescape(movie_name).strip()

    # Remove certificate
    movie_name = re.sub(
        r"\s*\([A-Z0-9+]+\)$",
        "",
        movie_name
    )

    language = unescape(match[3]).strip()

    movie_format = unescape(match[4]).strip()

    show_time = unescape(match[5]).strip()

    print(f"{i}. {movie_name}")
    print(f"   Language : {language}")
    print(f"   Format   : {movie_format}")
    print(f"   Event    : {event_code}")
    print(f"   Show     : {show_time}")
    print()