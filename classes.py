import requests
import datetime
import csv
import sqlite3
import re


file_name_csvstats = "todaystats.csv"
file_name_dbstats = "stats.db"


class Logs:
    def __init__(self, file_name_dblogs="logs.db") -> None:
        self.file_name = file_name_dblogs
        conn = sqlite3.connect(self.file_name)
        with conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS logs(
            log_id INTEGER primary key,
            user TEXT,
            function TEXT,
            message TEXT,
            time INTEGER
            );''')

    def addLog(self, new_log: dict) -> None:
        conn = sqlite3.connect(self.file_name)
        with conn:
            c = conn.cursor()
            c.execute('''INSERT into logs(user, function, message, time) VALUES(?,?,?,?)''', list(new_log.values()))

    def addLogs(self, new_logs: list) -> None:
        conn = sqlite3.connect(self.file_name)
        with conn:
            c = conn.cursor()
            for new_log in new_logs:
                c.execute('''INSERT into logs(user, function, message, time) VALUES(?,?,?,?)''', list(new_log.values()))

    def getLastFiveLogs(self) -> list:
        ans = []
        conn = sqlite3.connect(self.file_name)
        with conn:
            c = conn.cursor()
            c.execute('''SELECT user, function, message, time from logs''')
            data = c.fetchall()
            # print(data)
            if len(data) > 5:
                data = data[-1:-6:-1]
            for row in data:
                ans.append(
                    {"user": row[0], "function": row[1], "message": row[2], "time": row[3]}
                )
        # print(ans)
        return ans[::-1]

    def clean(self):
        conn = sqlite3.connect(self.file_name)
        with conn:
            c = conn.cursor()
            c.execute('''DELETE FROM logs''')


class CSVStats:
    date = datetime.date.today().strftime("%m-%d-%Y")

    def __init__(self, file_name) -> None:
        self.filename = file_name
        self.topfive = []
        self.fulldata = []
        self.conn = sqlite3.connect(file_name_dbstats)
        with self.conn:
            c = self.conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS topfive(
            date TEXT,
            province TEXT,
            new_infected INTEGER);''')
            c.execute(
                '''SELECT province, new_infected FROM topfive WHERE date = ? ORDER BY new_infected DESC;''',
                [self.date]
            )
            self.fulldata = []
            ans = c.fetchall()
            if len(ans) != 0:
                for row in ans:
                    self.topfive.append({"province": row[0], "new infected": row[1]})
                    self.status_code = 200
                self.topfive = self.topfive[0:5]
            else:
                r = requests.get(
                    f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{self.date}.csv')  # noqa
                self.status_code = r.status_code
                if self.status_code == 200:
                    with open(self.filename, "wb") as f:
                        f.write(r.content)

    def get_top_five_from_db(self) -> list:
        with self.conn:
            c = self.conn.cursor()
            c.execute(
                '''SELECT province, new_infected FROM topfive WHERE date = ? ORDER BY new_infected DESC;''',
                [self.date]
            )
            self.topfive = []
            ans = c.fetchall()
            if len(ans) != 0:
                for row in ans:
                    self.topfive.append({"province": row[0], "new infected": row[1]})
                    self.status_code = 200
            return self.topfive

    def changeRequest(self) -> None:
        self.topfive = self.get_top_five_from_db()
        if self.topfive:
            return
        r = requests.get(
            f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{self.date}.csv')# noqa
        self.status_code = r.status_code
        if self.status_code == 200:
            with open(self.filename, "wb") as f:
                f.write(r.content)

    def getTopFiveProvinces(self) -> list:
        if len(self.topfive) == 0:
            with open(self.filename, "r") as f:
                stats = csv.DictReader(f)
                top_five = []
                for row in stats:
                    place = row["Province_State"] + " " + row["Country_Region"] \
                        if row["Province_State"] != "" else row["Country_Region"]
                    new_infected = int(row["Confirmed"]) - int(row["Deaths"]) - int(row["Recovered"])
                    if len(top_five) == 0:
                        top_five.append({"province": place, "new infected": new_infected})
                    else:
                        for i in range(len(top_five)):
                            if top_five[i]["new infected"] <= new_infected:
                                top_five.insert(i, {"province": place, "new infected": new_infected})
                                break
                if len(top_five) < 5:
                    self.topfive = top_five
                else:
                    self.topfive = top_five[0:5]
                with self.conn:
                    c = self.conn.cursor()
                    for elem in self.topfive:
                        a = [self.date]
                        a += list(elem.values())
                        c.execute('''INSERT INTO topfive(date, province, new_infected) VALUES(?,?,?)''', a)
        return self.topfive


def parseDateFromString(string: str) -> str:
    pattern1 = '[0-3][0-9]\D+[0-1][0-9]\D+[0-2][0-9][0-9][0-9]+'# noqa
    pattern2 = '[0-3][0-9]\D+[0-1][0-9]' # noqa
    match1 = re.search(pattern1, string)
    match2 = re.search(pattern2, string)
    if match1:
        res = re.findall(pattern1, string)
        string = re.sub("\D", ' ', res[0])# noqa
        res = string.split()
        return res[1] + '-' + res[0] + '-' + res[2]
    elif match2:
        res = re.findall(pattern2, string)
        string = re.sub("\D", ' ', res[0])# noqa
        res = string.split()
        return res[1] + '-' + res[0] + '-' + str(datetime.date.today().year)
    else:
        return datetime.date.today().strftime("%m-%d-%Y")
