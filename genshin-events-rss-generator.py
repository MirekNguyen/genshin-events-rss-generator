import sys
from datetime import datetime, timedelta

import pytz
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

# Send a GET request to the website
url = "https://genshin-impact.fandom.com/wiki/Event"
event_type_to_check = [
    "web",
    "nameless honor",
    "indefinite",
    "login",
    "discount",
    "test run",
    "battle pass",
]
max_days = 7
timezone = pytz.timezone("Europe/Prague")
feed_id = "https://mirekng.com/rss/genshin-events.xml"
feed_title = "Genshin events"
feed_subtitle = "Genshi events"
feed_link_href = "https://genshin-impact.fandom.com/wiki/Event"


class Event:
    def __init__(self, title, start, end, event_type):
        self.title = title
        self.start = start
        self.end = end
        self.event_type = event_type


class TargetTable:
    def find_table(self):
        pass

    def extract_data(self):
        pass

    def __init__(self, url):
        response = requests.get(url)
        # Find the tbody element
        self.soup = BeautifulSoup(response.content, "html.parser")
        self.target_table = self.find_table()
        self.data = self.extract_data()


class TargetTableCustom(TargetTable):
    def find_table(self):
        tables = self.soup.find_all("table")
        for table in tables:
            # Find the previous sibling <h2> element of the table
            title_element = table.find_previous_sibling("h2").find(id="Current")
            if title_element and title_element.get_text() == "Current":
                return table
        return None

    def map_data(self, data):
        events = []
        for item in data:
            start, end = Tools.split_start_end_date(item[1])
            events.append(Event(item[0], start, end, item[2]))
        return events

    def filter_data(self, data):
        filtered_data = []
        for item in data:
            if (
                not Tools.check_item_type(item[2], event_type_to_check)
                or not Tools.check_item_date(item[1], max_days)
            ):
                continue
            filtered_data.append(item)
        return filtered_data

    def extract_data(self):
        data = []
        if not self.target_table or not self.target_table.find("tbody"):
            print("Target table could not be found")
            exit(1)
        tbody = self.target_table.find("tbody")
        for row in tbody.find_all("tr"):
            row_data = []
            for cell in row.find_all("td"):
                row_data.append(cell.text.strip())
            if row_data:
                data.append(row_data)
        return self.map_data(self.filter_data(data))


class Tools:
    @staticmethod
    def check_item_date(item_date, max_time):
        _, end = item_date.split(" – ")
        # Parse and format the end date
        end_date = datetime.strptime(end, "%B %d, %Y").date()
        # Calculate the timedelta between the two dates
        date_difference = end_date - datetime.now().date()
        if date_difference > timedelta(days=max_time):
            return False
        return True

    @staticmethod
    def split_start_end_date(item_date):
        start, end = item_date.split(" – ")
        start_date = datetime.strptime(start, "%B %d, %Y").date()
        end_date = datetime.strptime(end, "%B %d, %Y").date()
        return [start_date, end_date]

    @staticmethod
    def check_item_type(item_type, filter_words):
        if any(event_type.lower() in item_type.lower() for event_type in filter_words):
            return False
        return True


# Extract data from tbody and convert it to a JSON object
class Feed:
    def __init__(self, data):
        fg = FeedGenerator()
        fg.id(feed_id)
        fg.title(feed_title)
        fg.subtitle(feed_subtitle)
        fg.link(href=feed_link_href, rel="self")
        fg.language("en")
        for item in data:
            fe = fg.add_entry()
            fe.id(item.title)
            days_left = f"{(item.end - datetime.now().date()).days} days left"
            fe.title(days_left + " - " + item.title)
            fe.description(
                item.start.strftime("%Y-%m-%d") + " - " + item.end.strftime("%Y-%m-%d")
            )
            fe.pubDate(
                timezone.localize(datetime.combine(item.start, datetime.min.time()))
            )
        fg.rss_str(pretty=True)
        fg.rss_file(sys.argv[1])


table = TargetTableCustom(url)
Feed(table.data)
