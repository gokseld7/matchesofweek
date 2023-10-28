import requests
import threading
from bs4 import BeautifulSoup
from lxml import etree

# TODO: improve sortMatches
# TODO: write simple GUI witg pyqt


def getNextMatchWebRequest(teamName):
    url = f"https://www.google.com/search?q={teamName}+next+match"
    HEADERS = (
        {
            "User-Agent":
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    )

    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"Failed request for {teamName}!")
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    return etree.HTML(str(soup))


def getXPaths(data):
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


def getNextMatch(teamName, matches, lock):
    data = getNextMatchWebRequest(teamName)
    if data is not None:
        xPaths = getXPaths(data)
        try:
            lock.acquire()
            matches.append(
                {
                    "match": f'{data.xpath(xPaths["homeTeam"])[0].text} - {data.xpath(xPaths["awayTeam"])[0].text}',
                    "league": f'{data.xpath(xPaths["leagueName"])[0].text}',
                    "dateTime": f'{data.xpath(xPaths["dateTime"])[0].text}'
                }
            )
        except IndexError:
            print(f"Error parsing results for {teamName}")
        finally:
            lock.release()


def sortMatches(matches):
    # TODO: Add sorting according to time
    todaysMatches = []
    tomorrowsMatches = []
    otherMatches = []
    for match in matches:
        if "bugün" in match["dateTime"]:
            todaysMatches.append(match)
        elif "yarın" in match["dateTime"]:
            tomorrowsMatches.append(match)
        else:
            # TODO: Parse date and sort them too
            otherMatches.append(match)
    return todaysMatches + tomorrowsMatches + otherMatches


def showAllMatches(matches):
    matches = sortMatches(matches)
    for match in matches:
        print(20*"-")
        print(match["match"])
        print(match["league"])
        print(match["dateTime"])
        print(20*"-")


def main():
    teamNames = {"Fenerbahce", "PSV", "Borussia Dortmund", "Manchester City", "Real Madrid", "Leipzig"}
    matches = []
    threads = []
    lock = threading.Lock()

    for teamName in teamNames:
        threads.append(threading.Thread(target=getNextMatch, args=(teamName, matches, lock)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    showAllMatches(matches)


if __name__ == '__main__':
    main()
