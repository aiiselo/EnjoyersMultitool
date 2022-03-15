import unittest
from unittest import mock
from datetime import date
from classes import Logs, CSVStats, parseDateFromString


class TestLogs(unittest.TestCase):
    def setUp(self):
        self.logs = Logs('tests.db')

    def tearDown(self):
        self.logs.clean()

    def test_addLog(self):
        new_log = {
            "user": "Stepan", "function": "corona_stats", "message": "button", "time": "31-Mar-2020 (11:02:57.000000)"
        }
        self.logs.addLog(new_log)
        last_five_logs = self.logs.getLastFiveLogs()
        self.assertEqual(last_five_logs[0], new_log)

    def test_addLogs(self):
        new_logs = [
            {
                "user": "Stepan", "function": "corona_stats", "message": "button",
                "time": "31-Mar-2020 (11:02:57.000000)"
            },
            {
                "user": "Stepan", "function": "corona_stats", "message": "button",
                "time": "31-Mar-2020 (11:02:57.000000)"
            }
        ]
        self.logs.addLogs(new_logs)
        self.assertEqual(self.logs.getLastFiveLogs()[0:2], new_logs)

    def test_getLastFiveLogs(self):
        new_log = {
            "user": "Stepan", "function": "corona_stats", "message": "button", "time": "31-Mar-2020 (11:02:57.000000)"
        }
        last_log = {
            "user": "Stepan", "function": "corona_stats", "message": "button", "time": "01-Apr-2020 (12:20:00.000000)"
        }
        ans = []
        for _i in range(5):
            self.logs.addLog(new_log)
            ans.append(new_log)
        self.logs.addLog(last_log)
        ans.append(last_log)
        self.assertEqual(self.logs.getLastFiveLogs(), ans[1::])

    def test_getLastFiveLogs_len(self):
        self.assertTrue(len(self.logs.getLastFiveLogs()) <= 5)

    def test_magic_mock_getLastFiveLogs(self):
        self.logs.getLastFiveLogs = mock.MagicMock(return_value=1)
        self.assertEqual(self.logs.getLastFiveLogs(), 1)


class TestCSVStats(unittest.TestCase):
    def setUp(self):
        self.csvstats = CSVStats("test.csv")

    def tearDown(self):
        f = open("test.csv", "w")
        f.close()

    @mock.patch.object(CSVStats, 'getTopFiveProvinces', return_value=123)
    def test_mock_getTopFiveProvinces(self, mock_getTopFiveProvinces):
        self.assertEqual(self.csvstats.getTopFiveProvinces(), 123)

    def testParseDateFromString1(self):
        string = "11.04.2020"
        res = "04-11-2020"
        self.assertEqual(res, parseDateFromString(string))

    def testParseDateFromString2(self):
        string = "11..04.///2020"
        res = "04-11-2020"
        self.assertEqual(res, parseDateFromString(string))

    def testParseDateFromString3(self):
        string = "11..04"
        res = "04-11-2020"
        self.assertEqual(res, parseDateFromString(string))

    def testParseDateFromString4(self):
        string = "/corona_stats Хочу получить данные за 11..04.///2020"
        res = "04-11-2020"
        self.assertEqual(res, parseDateFromString(string))

    def testParseDateFromString5(self):
        string = "Данные за 41..04"
        res = date.today().strftime("%m-%d-%Y")
        self.assertEqual(res, parseDateFromString(string))


if __name__ == '__main__':
    unittest.main()
