import requests

url = "https://in.bookmyshow.com/api/movies-data/v5/showtimes-by-event/primary-dynamic"

params = {
    "etCodes": "ET00379311",
    "dateCode": "20260826",
    "isDesktop": "true",
    "regionCode": "CHEN",
    "xLocationShared": "false",
    "memberId": "",
    "lsId": "",
    "subCode": "",
    "appCode": "WEB",
    "language": "hindi",
    "refEventCode": "ET00379311"
}

headers = {
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
}

response = requests.get(
    url,
    params=params,
    headers=headers
)
print("Status code:", response.status_code)

data = response.json()

showtime_widgets = data["data"]["showtimeWidgets"]

for widget in showtime_widgets:

    if widget.get("type") != "groupList":
        continue

    for venue_group in widget.get("data", []):

        if venue_group.get("type") != "venueGroup":
            continue

        for venue in venue_group.get("data", []):

            if venue.get("type") != "venue-card":
                continue

            venue_info = venue.get("additionalData", {})

            venue_name = venue_info.get("venueName")
            venue_code = venue_info.get("venueCode")

            # Only Cinepolis BSR Mall
            if venue_code != "CBMC":
                continue

            for section in venue.get("showtimesSections", []):

                for show in section.get("showtimes", []):

                    show_time = show.get("title")

                    additional_data = show.get("additionalData", {})
                    session_id = additional_data.get("sessionId")

                    gesture = show.get("customGestureCTA", {})

                    bottom_sheet_data = (
                        gesture
                        .get("additionalData", {})
                        .get("bottomSheetData", {})
                    )

                    widgets = bottom_sheet_data.get("widgets", [])

                    for seat_widget in widgets:

                        variable_data = seat_widget.get(
                            "variableData", {}
                        )

                        seat_type = variable_data.get("seatType")
                        seat_availability = variable_data.get(
                            "seatAvalibility"
                        )
                        seat_cost = variable_data.get("seatCost")

                        # Front seat = NORMAL
                        if (
                            seat_type == "NORMAL"
                            and seat_availability != "SOLD OUT"
                        ):
                            print(
                                f"FRONT SEAT AVAILABLE | "
                                f"Time: {show_time} | "
                                f"Session: {session_id} | "
                                f"Status: {seat_availability} | "
                                f"Price: {seat_cost}"
                            )