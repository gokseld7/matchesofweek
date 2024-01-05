import requests
import threading
import datetime as dt
from bs4 import BeautifulSoup
from lxml import etree
from typing import Union
from userconf import favourite_teams

# TODO: prepare to get web results all in English and resolve everything in English
# TODO: after converting English, set the dd/mm or mm/dd format
# TODO: write simple GUI with pyqt
# TODO: Dockerize the app to make this project os agnostic
# TODO: Is there any way to make get_next_matches better?
#       Maybe getNextMatch as an individual function
# TODO: Find a better parsing method from xpath


def get_request(url: str, headers: dict) -> Union[str, None]:
    max_retries = 3
    for i in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
    return None


def get_next_match_web_request(teamName: str) -> Union[None, etree._Element]:
    teamName = teamName.replace(" ", "+")
    url = f"https://www.google.com/search?q={teamName}+next+match"
    headers = (
        {
            "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    )

    response = get_request(url, headers)
    if response is None:
        print(f"Failed request for {teamName}!")
        return None

    soup = BeautifulSoup(response, "html.parser")
    return etree.HTML(str(soup))


def get_xpaths(data: etree._Element) -> dict:
    xpaths = dict()
    index = 3
    common_path = f"//*[@id='sports-app']/div/div[3]/div[1]/div[{index}]/div/div/div/div[1]/div"

    if not data.xpath(common_path):
        common_path = f"//*[@id='sports-app']/div/div[3]/div[1]/div[{index}]/div/div/div/div[2]/div"

    home_team = f"{common_path}/div[2]/div[1]/div/div[1]/div[2]/div/span"
    if not data.xpath(home_team):
        index = 4
        common_path = f"//*[@id='sports-app']/div/div[3]/div[1]/div[{index}]/div/div/div/div[1]/div"

    xpaths["homeTeam"] = f"{common_path}/div[2]/div[1]/div/div[1]/div[2]/div/span"

    xpaths["awayTeam"] = f"{common_path}/div[2]/div[1]/div/div[3]/div[2]/div/span"
    xpaths["leagueName"] = f"{common_path}/div[1]/div/span[1]/span[1]/span"
    xpaths["dateTime"] = f"{common_path}/div[1]/div/span[2]"
    return xpaths


def parse_date_time(date_time_str: str) -> dt.datetime:
    date_time_str = date_time_str.lower()
    hour, minute = date_time_str.split(',')[1].strip().split(':')
    hour = int(hour)
    minute = int(minute)

    if '/' in date_time_str:
        day, month = date_time_str.split()[0].split('/')
        day = int(day)
        month = int(month)
        date_time = dt.datetime(dt.datetime.now().year, month, day, hour, minute, 0, 0)
        return date_time

    date_time = dt.datetime.now()
    if "yarın" in date_time_str or "tomorrow" in date_time_str:
        date_time = date_time + dt.timedelta(days=1)

    date_time = date_time.replace(hour=hour)
    date_time = date_time.replace(minute=minute)
    date_time = date_time.replace(second=0).replace(microsecond=0)

    return date_time


def get_next_matches(team_name: str, matches: list, lock: threading.Lock) -> None:
    data = get_next_match_web_request(team_name)
    if data is not None:
        xpaths = get_xpaths(data)
        lock.acquire()
        try:
            date_time = parse_date_time(f"{data.xpath(xpaths['dateTime'])[0].text}")
            matches.append(
                {
                    "match":
                        f"{data.xpath(xpaths['homeTeam'])[0].text} - {data.xpath(xpaths['awayTeam'])[0].text}",
                    "league":
                        f"{data.xpath(xpaths['leagueName'])[0].text}",
                    "dateTime": date_time
                }
            )
        except IndexError:
            print(f"Error parsing results for {team_name}")
        finally:
            lock.release()


def show_all_matches(matches: list) -> None:
    matches = sorted(matches, key=lambda x: x["dateTime"])
    for match in matches:
        print(20*"-")
        print(match["match"])
        print(match["league"])
        print(match["dateTime"].strftime("%c"))
        print(20*"-")


def main():
    if type(favourite_teams) != set:
        print("Favourite teams in userconf.py is not a set, please edit it and try again.")
        print("Example userconf.py: favourite_teams =  {'Fenerbahce', 'PSV'}")
        return
    matches = []
    threads = []
    lock = threading.Lock()

    for team_name in favourite_teams:
        threads.append(threading.Thread(target=get_next_matches, args=(team_name, matches, lock)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    show_all_matches(matches)


if __name__ == '__main__':
    main()
