import requests
import threading
import datetime as dt
from bs4 import BeautifulSoup
from lxml import etree
from typing import Union
from userconf import favouriteTeams

# TODO: prepare to get web results all in English and resolve everything in English
# TODO: after converting English, set the dd/mm or mm/dd format
# TODO: write simple GUI with pyqt
# TODO: Dockerize the app to make this project os agnostic
# TODO: Is there any way to make getNextMatches better? Maybe getNextMatch as an individual function


def sendGetRequest(url: str, headers: dict) -> Union[str, None]:
    max_retries = 3
    for i in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
    return None


def getNextMatchWebRequest(teamName: str) -> Union[None, etree._Element]:
    teamName = teamName.replace(" ", "+")
    url = f"https://www.google.com/search?q={teamName}+next+match"
    headers = (
        {
            "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    )

    response = sendGetRequest(url, headers)
    if response is None:
        print(f"Failed request for {teamName}!")
        return None

    soup = BeautifulSoup(response, "html.parser")
    return etree.HTML(str(soup))


def getXPaths(data: etree._Element) -> dict:
    xPaths = dict()
    index = 3
    commonPath = f"//*[@id='sports-app']/div/div[3]/div[1]/div[{index}]/div/div/div/div[1]/div"

    homeTeam = f"{commonPath}/div[2]/div[1]/div/div[1]/div[2]/div/span"
    if not data.xpath(homeTeam):
        index = 4
        commonPath = f"//*[@id='sports-app']/div/div[3]/div[1]/div[{index}]/div/div/div/div[1]/div"

    xPaths["homeTeam"] = f"{commonPath}/div[2]/div[1]/div/div[1]/div[2]/div/span"
    xPaths["awayTeam"] = f"{commonPath}/div[2]/div[1]/div/div[3]/div[2]/div/span"
    xPaths["leagueName"] = f"{commonPath}/div[1]/div/span[1]/span[1]/span"
    xPaths["dateTime"] = f"{commonPath}/div[1]/div/span[2]"
    return xPaths


def parseDateTime(dateTimeStr: str) -> dt.datetime:
    dateTimeStr = dateTimeStr.lower()
    hour, minute = dateTimeStr.split(',')[1].strip().split(':')
    hour = int(hour)
    minute = int(minute)

    if '/' in dateTimeStr:
        day, month = dateTimeStr.split()[0].split('/')
        day = int(day)
        month = int(month)
        dateTime = dt.datetime(dt.datetime.now().year, month, day, hour, minute, 0, 0)
        return dateTime

    dateTime = dt.datetime.now()
    if "yarın" in dateTimeStr or "tomorrow" in dateTimeStr:
        dateTime = dateTime + dt.timedelta(days=1)

    dateTime = dateTime.replace(hour=hour)
    dateTime = dateTime.replace(minute=minute)
    dateTime = dateTime.replace(second=0).replace(microsecond=0)

    return dateTime


def getNextMatches(teamName: str, matches: list, lock: threading.Lock) -> None:
    data = getNextMatchWebRequest(teamName)
    if data is not None:
        xPaths = getXPaths(data)
        lock.acquire()
        try:
            dateTime = parseDateTime(f"{data.xpath(xPaths['dateTime'])[0].text}")
            matches.append(
                {
                    "match": f"{data.xpath(xPaths['homeTeam'])[0].text} - {data.xpath(xPaths['awayTeam'])[0].text}",
                    "league": f"{data.xpath(xPaths['leagueName'])[0].text}",
                    "dateTime": dateTime
                }
            )
        except IndexError:
            print(f"Error parsing results for {teamName}")
        finally:
            lock.release()


def showAllMatches(matches: list) -> None:
    matches = sorted(matches, key=lambda x: x["dateTime"])
    for match in matches:
        print(20*"-")
        print(match["match"])
        print(match["league"])
        print(match["dateTime"].strftime("%c"))
        print(20*"-")


def main():
    if type(favouriteTeams) != set:
        print("Favourite teams in userconf.py is not a set, please edit it and try again.")
        print("Example userconf.py: favouriteTeams =  {'Fenerbahce', 'PSV'}")
        return
    matches = []
    threads = []
    lock = threading.Lock()

    for teamName in favouriteTeams:
        threads.append(threading.Thread(target=getNextMatches, args=(teamName, matches, lock)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    showAllMatches(matches)


if __name__ == '__main__':
    main()
