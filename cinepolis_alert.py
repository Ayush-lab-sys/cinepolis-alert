import requests
import re
import time
import threading
import os
from html import unescape
from datetime import datetime
import json
import os
import requests
import re

STATE_FILE = "state.json"


def load_state():

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {
            "movie": None,
            "event_codes": [],
            "language": "english",
            "date": "2026-08-27",
            "cinema": "CBMC",
            "monitoring": False,
            "last_available": [],
            "telegram_offset": None
        }


def save_state():

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            config,
            f,
            indent=4
        )

# ============================================================
# TELEGRAM
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Your Telegram chat ID
TELEGRAM_CHAT_ID = "5314697440"


# ============================================================
# CONFIGURATION
# ============================================================

config = load_state()

last_available = set(
    config.get(
        "last_available",
        []
    )
)


# ============================================================
# BOOKMYSHOW
# ============================================================

BMS_URL = (
    "https://in.bookmyshow.com/api/movies-data/v5/"
    "showtimes-by-event/primary-dynamic"
)

BSR_URL = (
    "https://in.bookmyshow.com/cinemas/chennai/"
    "cinepolis-bsr-mall-omr-thoraipakkam/"
    "buytickets/CBMC/{date}"
)


HEADERS = {
    "x-app-code": "WEB",
    "x-geohash": "tf3",
    "x-latitude": "13.056",
    "x-longitude": "80.206",
    "x-region-slug": "chennai",
    "x-region-code": "CHEN",
    "x-platform-code": "WEB",
    "x-platform": "WEB",
    "x-location-selection": "manual",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://in.bookmyshow.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}


# ============================================================
# DATE
# ============================================================

def convert_date(date_string):

    try:
        return datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).strftime("%Y%m%d")

    except ValueError:
        return None


# ============================================================
# TELEGRAM SEND
# ============================================================

def send_telegram(message, chat_id=None, reply_markup=None):

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set.")
        return False

    if chat_id is None:
        chat_id = TELEGRAM_CHAT_ID

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": chat_id,
        "text": message
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=20
        )

        data = response.json()

        if not data.get("ok"):
            print("Telegram error:", data)
            return False

        return True

    except Exception as e:

        print("Telegram error:", e)
        return False
# ============================================================
# GET MOVIES AT BSR
# ============================================================

def get_bsr_movies():

    date_code = convert_date(
        config["date"]
    )

    if not date_code:

        print(
            "Invalid date:",
            config["date"]
        )

        return []

    url = BSR_URL.format(
        date=date_code
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

    except Exception as e:

        print(
            "BSR request error:",
            e
        )

        return []

    print(
        "BSR Status:",
        response.status_code
    )

    if response.status_code != 200:

        return []

    html = response.text

    pattern = re.compile(
        r'<a href="/movies/chennai/[^"]+/(ET\d+)"'
        r'[^>]*>(.*?)</a>'
        r'.*?'
        r'<a href="/explore/movies\?languages=([^"]+)"'
        r'[^>]*>(.*?)</a>'
        r'.*?'
        r'<span[^>]*>([^<]+)</span>',
        re.DOTALL
    )

    matches = pattern.findall(html)

    movies = []

    for match in matches:

        event_code = match[0]

        movie_name = re.sub(
            r"<.*?>",
            "",
            match[1]
        )

        movie_name = unescape(
            movie_name
        ).strip()

        movie_name = re.sub(
            r"\s*\([A-Z0-9+]+\)$",
            "",
            movie_name
        )

        language = unescape(
            match[3]
        ).strip()

        movie_format = unescape(
            match[4]
        ).strip()

        movie_format = movie_format.lstrip(
            ", "
        )

        movies.append({
            "movie": movie_name,
            "language": language,
            "format": movie_format,
            "event_code": event_code
        })

    return movies


# ============================================================
# /MOVIE
# ============================================================

def list_movies(chat_id):

    movies = get_bsr_movies()

    if not movies:

        send_telegram(
            "❌ Could not get movies.\n\n"
            f"📅 Date: {config['date']}",
            chat_id
        )

        return

    grouped = {}

    for movie in movies:

        name = movie["movie"]

        key = name.lower()

        if key not in grouped:

            grouped[key] = {
                "name": name,
                "languages": set()
            }

        grouped[key]["languages"].add(
            movie["language"]
        )

    message = (
        "🎬 MOVIES AT CINEPOLIS BSR\n\n"
        f"📅 Date: {config['date']}\n"
        f"🌐 Language: "
        f"{config['language'].title()}\n\n"
        "👇 Select a movie:"
    )

    keyboard = []

    for movie in grouped.values():

        name = movie["name"]

        keyboard.append([
            {
                "text": f"🎬 {name}",
                "callback_data": f"movie:{name}"
            }
        ])

    reply_markup = {
        "inline_keyboard": keyboard
    }

    send_telegram(
        message,
        chat_id,
        reply_markup
    )
# ============================================================
# SELECT MOVIE
# ============================================================

def select_movie(movie_name):

    movies = get_bsr_movies()

    requested = movie_name.strip().lower()

    # First try exact movie + selected language
    matching = [
        movie
        for movie in movies
        if movie["movie"].strip().lower() == requested
        and movie["language"].strip().lower()
        == config["language"].strip().lower()
    ]

    # If exact match failed, try partial movie + language
    if not matching:

        matching = [
            movie
            for movie in movies
            if requested in movie["movie"].strip().lower()
            and movie["language"].strip().lower()
            == config["language"].strip().lower()
        ]

    # --------------------------------------------------------
    # IMPORTANT FALLBACK
    # --------------------------------------------------------
    # If movie exists but selected language doesn't match,
    # show which languages are actually available.
    if not matching:

        movie_versions = [
            movie
            for movie in movies
            if requested in movie["movie"].strip().lower()
        ]

        if movie_versions:

            languages = sorted(
                set(
                    movie["language"]
                    for movie in movie_versions
                )
            )

            return (
                "❌ Movie found, but not in the selected language.\n\n"
                f"🎬 {movie_versions[0]['movie']}\n"
                f"🌐 Selected: {config['language'].title()}\n"
                f"📅 {config['date']}\n\n"
                "Available languages:\n"
                +
                "\n".join(
                    f"• {language}"
                    for language in languages
                )
                +
                "\n\n"
                "Change language with:\n"
                "/language <language>"
            )

        return (
            "❌ Movie not found.\n\n"
            f"🎬 {movie_name}\n"
            f"📅 {config['date']}\n\n"
            "Use /movie to see the available movies."
        )

    config["movie"] = matching[0]["movie"]

    config["event_codes"] = [
        {
            "event_code": movie["event_code"],
            "format": movie["format"]
        }
        for movie in matching
    ]

    global last_available
    last_available.clear()

    # ========================================================
    # IMMEDIATE CHECK
    # ========================================================

    current_results = []

    print("\nImmediate availability check...")

    for event_info in config["event_codes"]:

        print(
            "Checking:",
            event_info["event_code"],
            event_info["format"]
        )

        results = check_availability(event_info)

        current_results.extend(results)

    config["monitoring"] = True
    config["last_available"] = list(
    last_available
    )

    save_state()

    # ========================================================
    # RESPONSE
    # ========================================================

    message = (
        "✅ MOVIE SELECTED\n\n"
        f"🎬 {config['movie']}\n"
        f"🌐 {config['language'].title()}\n"
        f"📅 {config['date']}\n\n"
        "🎞️ VERSIONS:\n"
    )

    for movie in matching:

        message += (
            f"• {movie['format'] or '2D'}"
            f" → {movie['event_code']}\n"
        )

    # Current availability
    if current_results:

        message += (
            "\n🟢 FRONT SEAT CURRENTLY AVAILABLE!\n\n"
        )

        for result in current_results:

            message += (
                f"🕐 Show: {result['time']}\n"
                f"🎞️ Format: {result['format'] or '2D'}\n"
                f"💺 Front seat: {result['status']}\n"
                f"💰 Price: ₹{result['price']}\n"
                f"🎟️ Session: {result['session']}\n\n"
            )

    else:

        message += (
            "\n🔴 FRONT SEAT CURRENTLY NOT AVAILABLE.\n"
        )

    message += (
        "\n🔔 Monitoring started.\n"
        "⏱ Checking every 5 minutes."
    )

    return message

# ============================================================
# CHECK FRONT SEATS
# ============================================================

def handle_callback_query(callback_query):

    callback_id = callback_query["id"]

    chat_id = callback_query["message"]["chat"]["id"]

    data = callback_query.get("data", "")

    # Tell Telegram that the button was clicked
    answer_url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    )

    try:

        requests.post(
            answer_url,
            json={
                "callback_query_id": callback_id
            },
            timeout=10
        )

    except Exception as e:

        print(
            "Callback answer error:",
            e
        )

    # --------------------------------------------------------
    # MOVIE BUTTON
    # --------------------------------------------------------

    if data.startswith("movie:"):

        movie_name = data[
            len("movie:"):
        ]

        print(
            "Movie button clicked:",
            movie_name
        )

        result = select_movie(
            movie_name
        )

        send_telegram(
            result,
            chat_id
        )

def check_availability(
    event_info
):

    event_code = event_info[
        "event_code"
    ]

    movie_format = event_info[
        "format"
    ]

    date_code = convert_date(
        config["date"]
    )

    params = {
        "etCodes": event_code,
        "dateCode": date_code,
        "isDesktop": "true",
        "regionCode": "CHEN",
        "xLocationShared": "false",
        "memberId": "",
        "lsId": "",
        "subCode": "",
        "appCode": "WEB",
        "language": config["language"],
        "refEventCode": event_code
    }

    try:

        response = requests.get(
            BMS_URL,
            params=params,
            headers=HEADERS,
            timeout=20
        )

    except Exception as e:

        print(
            "API request error:",
            e
        )

        return []

    if response.status_code != 200:

        print(
            "API status:",
            response.status_code
        )

        return []

    try:

        data = response.json()

    except Exception:

        return []

    results = []

    widgets = (
        data
        .get("data", {})
        .get("showtimeWidgets", [])
    )

    for widget in widgets:

        if widget.get(
            "type"
        ) != "groupList":

            continue

        for venue_group in widget.get(
            "data", []
        ):

            if venue_group.get(
                "type"
            ) != "venueGroup":

                continue

            for venue in venue_group.get(
                "data", []
            ):

                if venue.get(
                    "type"
                ) != "venue-card":

                    continue

                venue_info = venue.get(
                    "additionalData",
                    {}
                )

                if venue_info.get(
                    "venueCode"
                ) != config["cinema"]:

                    continue

                for section in venue.get(
                    "showtimesSections",
                    []
                ):

                    for show in section.get(
                        "showtimes",
                        []
                    ):

                        show_time = show.get(
                            "title"
                        )

                        additional = show.get(
                            "additionalData",
                            {}
                        )

                        session_id = additional.get(
                            "sessionId"
                        )

                        gesture = show.get(
                            "customGestureCTA",
                            {}
                        )

                        bottom_sheet = (
                            gesture
                            .get("additionalData", {})
                            .get("bottomSheetData", {})
                        )

                        seat_widgets = (
                            bottom_sheet
                            .get("widgets", [])
                        )

                        for seat_widget in seat_widgets:

                            variable = (
                                seat_widget
                                .get(
                                    "variableData",
                                    {}
                                )
                            )

                            seat_type = variable.get(
                                "seatType"
                            )

                            availability = variable.get(
                                "seatAvalibility"
                            )

                            price = variable.get(
                                "seatCost"
                            )

                            # BSR currently calls the
                            # front-seat category NORMAL.
                            if (
                                seat_type == "NORMAL"
                                and
                                availability != "SOLD OUT"
                            ):

                                results.append({
                                    "time": show_time,
                                    "session": session_id,
                                    "status": availability,
                                    "price": price,
                                    "event_code": event_code,
                                    "format": movie_format
                                })

    return results


# ============================================================
# SEND AVAILABILITY NOTIFICATION
# ============================================================

def notify_available(result):

    unique_id = (
        f"{config['movie']}|"
        f"{config['date']}|"
        f"{result['event_code']}|"
        f"{result['session']}"
    )

    global last_available

    if unique_id in last_available:

        print(
            "Already notified:",
            unique_id
        )

        return

    last_available.add(
        unique_id
    )
    config["last_available"] = list(
    last_available
    )

    save_state()

    message = (
        "🎟️ FRONT SEAT AVAILABLE!\n\n"
        f"🎬 {config['movie']}\n"
        f"🌐 {config['language'].title()}\n"
        f"📅 {config['date']}\n\n"
        f"🕐 Show: {result['time']}\n"
        f"🎞️ Format: {result['format'] or '2D'}\n"
        f"💺 Front seat: {result['status']}\n"
        f"💰 Price: {result['price']}\n\n"
        f"Session: {result['session']}"
    )

    send_telegram(
        message
    )


# ============================================================
# MONITOR LOOP
# ============================================================

def monitor_once():

    if not config["monitoring"]:

        print("Monitoring is OFF.")

        return

    if not config["event_codes"]:

        print("No event codes configured.")

        return

    print(
        "\nChecking BookMyShow..."
    )

    for event_info in config["event_codes"]:

        print(
            "Checking:",
            event_info["event_code"],
            event_info["format"]
        )

        results = check_availability(
            event_info
        )

        for result in results:

            print(
                "FRONT SEAT AVAILABLE | "
                f"Time: {result['time']} | "
                f"Format: {result['format']} | "
                f"Status: {result['status']} | "
                f"Price: {result['price']}"
            )

            notify_available(result)

save_state()

# ============================================================
# TELEGRAM API
# ============================================================

def get_updates():

    offset = config.get(
        "telegram_offset"
    )

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_BOT_TOKEN}/getUpdates"
    )

    params = {
        "timeout": 5
    }

    if offset is not None:

        params["offset"] = offset

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        return response.json()

    except Exception as e:

        print(
            "Telegram error:",
            e
        )

        return {
            "ok": False
        }


# ============================================================
# COMMAND HANDLER
# ============================================================

def handle_message(
    chat_id,
    text
):

    text = text.strip()

    # --------------------------------------------------------
    # /START
    # --------------------------------------------------------

    if text == "/start":

        send_telegram(
            "🎬 Cinepolis BSR Alert Bot\n\n"
            "Commands:\n\n"
            "/movie - List movies\n"
            "/movie Movie Name - Select movie\n"
            "/date YYYY-MM-DD - Set date\n"
            "/language english - Set language\n"
            "/status - Show configuration\n"
            "/stop - Stop monitoring"
        )

        return

    # --------------------------------------------------------
    # /MOVIE
    # --------------------------------------------------------

    if text.lower() == "/movie":

        list_movies(chat_id)

        return

    if text.lower().startswith(
        "/movie "
    ):

        movie_name = text[
            len("/movie "):
        ].strip()

        result = select_movie(
            movie_name
        )

        send_telegram(
            result
        )

        return

    # --------------------------------------------------------
    # /DATE
    # --------------------------------------------------------

    if text.lower().startswith(
        "/date "
    ):

        date_value = text[
            len("/date "):
        ].strip()

        date_code = convert_date(
            date_value
        )

        if not date_code:

            send_telegram(
                "❌ Invalid date.\n\n"
                "Use:\n"
                "/date 2026-08-27"
            )

            return

        config["date"] = date_value

        config["movie"] = None
        config["event_codes"] = []
        config["monitoring"] = False

        last_available.clear()

        config["last_available"] = []

        save_state()

        send_telegram(
            "✅ Date changed.\n\n"
            f"📅 {date_value}\n\n"
            "Use /movie to see movies "
            "available on this date.",
            chat_id
        )

        return

    # --------------------------------------------------------
    # /LANGUAGE
    # --------------------------------------------------------

    if text.lower().startswith(
        "/language "
    ):

        language = text[
            len("/language "):
        ].strip().lower()

        if not language:

            send_telegram(
                "❌ Please specify a language.\n\n"
                "Example:\n"
                "/language english"
            )

            return

        config["language"] = language

        config["movie"] = None
        config["event_codes"] = []
        config["monitoring"] = False

        last_available.clear()

        config["last_available"] = []

        save_state()

        send_telegram(
            "✅ Language changed.\n\n"
            f"🌐 {language.title()}\n\n"
            "Use /movie to select a movie."
        )

        return

    # --------------------------------------------------------
    # /STATUS
    # --------------------------------------------------------

    if text == "/status":

        if config["movie"]:

            versions = "\n".join(
                f"• {item['format'] or '2D'}"
                for item in config[
                    "event_codes"
                ]
            )

        else:

            versions = "None"

        send_telegram(
            "⚙️ CURRENT CONFIGURATION\n\n"
            f"🎬 Movie: "
            f"{config['movie'] or 'Not selected'}\n"
            f"🌐 Language: "
            f"{config['language'].title()}\n"
            f"📅 Date: "
            f"{config['date']}\n"
            f"🏢 Cinema: Cinepolis BSR\n\n"
            f"🎞️ Versions:\n"
            f"{versions}\n\n"
            f"🔔 Monitoring: "
            f"{'ON' if config['monitoring'] else 'OFF'}"
        )

        return

    # --------------------------------------------------------
    # /STOP
    # --------------------------------------------------------

    if text == "/stop":

        config["monitoring"] = False

        save_state()

        send_telegram(
            "🛑 Monitoring stopped.",
            chat_id
        )

        return

    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------

    send_telegram(
        "❓ Unknown command.\n\n"
        "Use /start to see available commands."
    )


# ============================================================
# TELEGRAM BOT LOOP
# ============================================================


def process_telegram_updates():

    result = get_updates()

    if not result.get("ok"):

        return

    for update in result.get(
        "result",
        []
    ):

        config["telegram_offset"] = (
            update["update_id"] + 1
        )

        message = update.get(
            "message"
        )

        if message:

            chat_id = message[
                "chat"
            ]["id"]

            text = message.get(
                "text",
                ""
            )

            print(
                "Telegram:",
                text
            )

            handle_message(
                chat_id,
                text
            )

        callback_query = update.get(
            "callback_query"
        )

        if callback_query:

            print(
                "Telegram button:",
                callback_query.get("data")
            )

            handle_callback_query(
                callback_query
            )

    save_state()
# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    if not TELEGRAM_BOT_TOKEN:

        print(
            "ERROR: TELEGRAM_BOT_TOKEN "
            "is not set."
        )

        exit()

    print(
        "\n================================"
    )

    print(
        "CINEPOLIS BSR GITHUB MONITOR"
    )

    print(
        "================================"
    )

    print(
        "Date:",
        config["date"]
    )

    print(
        "Movie:",
        config["movie"]
    )

    print(
        "Monitoring:",
        config["monitoring"]
    )

    # -----------------------------------------
    # Process Telegram commands/buttons
    # -----------------------------------------

    process_telegram_updates()

    # -----------------------------------------
    # Check current movie availability
    # -----------------------------------------

    monitor_once()

    # -----------------------------------------
    # Save everything
    # -----------------------------------------

    config["last_available"] = list(
        last_available
    )

    save_state()

    print(
        "\nRun completed."
    )