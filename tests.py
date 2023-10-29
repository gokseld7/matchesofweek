import unittest
import main
import datetime as dt
from lxml import etree
from threading import Lock


class TestMatchesOfWeek(unittest.TestCase):

    def test_sendGetRequest(self):
        url = "https://www.google.com"
        headers = (
            {
                "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        )
        self.assertIsNotNone(main.sendGetRequest(url, headers))

    def test_getNextMatchWebRequest(self):
        teamName = "Fenerbahce"
        self.assertIsNotNone(main.getNextMatchWebRequest(teamName))

    def test_getXPaths(self):
        testValues = [{"teamName": "PSV", "index": 3}, {"teamName": "Barcelona", "index": 4}]
        for vals in testValues:
            commonPath = f"//*[@id='sports-app']/div/div[3]/div[1]/div[{vals['index']}]/div/div/div/div[1]/div"
            with open(f"testInputs/{vals['teamName']}SampleResult_index{vals['index']}.txt") as f:
                result = main.getXPaths(etree.HTML(f.read()))

            self.assertEqual(result["homeTeam"],
                             f"{commonPath}/div[2]/div[1]/div/div[1]/div[2]/div/span")
            self.assertEqual(result["awayTeam"],
                             f"{commonPath}/div[2]/div[1]/div/div[3]/div[2]/div/span")
            self.assertEqual(result["leagueName"],
                             f"{commonPath}/div[1]/div/span[1]/span[1]/span")
            self.assertEqual(result["dateTime"],
                             f"{commonPath}/div[1]/div/span[2]")

    def test_parseDateTime(self):
        testValues = ["Bugün, 19:00", "Yarın, 17:30", "4/11 Cmt, 19:00"]
        expectedResults = []
        dateTime = dt.datetime.now().replace(second=0).replace(microsecond=0)
        expectedResults.append(dateTime.replace(hour=19).replace(minute=0))

        dateTime + dt.timedelta(days=1)
        expectedResults.append(dateTime.replace(hour=17).replace(minute=30))

        expectedResults.append(dt.datetime(dt.datetime.now().year, 11, 4, 19, 0, 0, 0))

        for i in range(3):
            self.assertEqual(main.parseDateTime(testValues[i]), expectedResults[i])

    def test_getNextMatch(self):
        # NOTE: Before doing this test,
        #       please update expectedResult according to the next match information.
        teamNames = ["PSV", "Fenerbahce"]
        expectedResult = [
                            {
                             'match': 'Heracles - PSV',
                             'league': 'Eredivisie',
                             'dateTime': dt.datetime(2023, 11, 4, 18, 30)
                            },

                            {
                             'match': 'Fenerbahçe - Trabzonspor',
                             'league': 'Süper Lig',
                             'dateTime': dt.datetime(2023, 11, 4, 19, 0)
                            },
                         ]
        matches = []
        for teamName in teamNames:
            main.getNextMatches(teamName, matches, Lock())

        self.assertEqual(matches, expectedResult)

    def test_showAllMatches(self):
        pass


if __name__ == '__main__':
    unittest.main()
