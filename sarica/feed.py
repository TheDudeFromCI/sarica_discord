import os
import feedparser
from .sql import Database


class Chapter:
    def __init__(self, index, name, story, link, chapter_id):
        self.index = index
        self.name = name
        self.story = story
        self.link = link
        self.chapter_id = chapter_id


def get_latest_chapter_rr():
    fiction_id = os.getenv("RR_FICTION_ID")
    feed_url = f"https://www.royalroad.com/syndication/103454"
    feed = feedparser.parse(feed_url)

    latest_name = feed.entries[0].title
    latest_link = feed.entries[0].link
    latest_id = feed.entries[0].guid

    title_parts = latest_name.split(" - ")
    story = title_parts[0].strip()
    index = int(title_parts[1].strip().split(" ")[1])
    name = title_parts[2].strip()

    return Chapter(index, name, story, latest_link, latest_id)


def query_rr(db: Database):
    chapter = get_latest_chapter_rr()
    latest_chapter_id = db.get("latest_chapter_id")

    # If the latest chapter is not in the database, add it, but don't return anything
    if latest_chapter_id is None:
        db.set("latest_chapter_id", chapter.chapter_id)
        print(f"Added last chapter to Database: {chapter.name}", flush=True)
        return

    # If the latest chapter is different from the one in the database, update the database and return the new chapter
    elif latest_chapter_id != chapter.chapter_id:
        db.set("latest_chapter_id", chapter.chapter_id)
        print(f"New chapter: {chapter.name}", flush=True)
        return chapter
