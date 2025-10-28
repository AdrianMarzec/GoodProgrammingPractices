from typing import List
import csv
import os
from fastapi import FastAPI

app = FastAPI()

class Movie:
    def __init__(self, movieId: int, title: str, genres: List[str]):
        self.movieId = movieId
        self.title = title
        self.genres = genres


class Link:
    def __init__(self, movieId: int, imdbId: str, tmdbId: str):
        self.movieId = movieId
        self.imdbId = imdbId
        self.tmdbId = tmdbId


class Rating:
    def __init__(self, userId: int, movieId: int, rating: float, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.rating = rating
        self.timestamp = timestamp


class Tag:
    def __init__(self, userId: int, movieId: int, tag: str, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.tag = tag
        self.timestamp = timestamp


def read_csv(file_path: str) -> List[dict]:
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


#http://127.0.0.1:8000/movies
@app.get("/movies")
def get_movies():
    movies = []
    csv_file = os.path.join("database", "movies.csv")
    
    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            #obiekt Movie dla każdego wiersza
            movie = Movie(
                movieId=int(row["movieId"]),
                title=row["title"],
                genres=row["genres"].split("|")  #zamiana na listę
            )
            movies.append(movie.__dict__)  #serializacja do słownika

    return movies


@app.get("/links")
def get_links():
    rows = read_csv(os.path.join("database", "links.csv"))
    links = [
        Link(
            movieId=int(row["movieId"]),
            imdbId=row["imdbId"],
            tmdbId=row["tmdbId"]
        ).__dict__ for row in rows
    ]
    return links


@app.get("/ratings")
def get_ratings():
    rows = read_csv(os.path.join("database", "ratings.csv"))
    ratings = [
        Rating(
            userId=int(row["userId"]),
            movieId=int(row["movieId"]),
            rating=float(row["rating"]),
            timestamp=int(row["timestamp"])
        ).__dict__ for row in rows
    ]
    return ratings


@app.get("/tags")
def get_tags():
    rows = read_csv(os.path.join("database", "tags.csv"))
    tags = [
        Tag(
            userId=int(row["userId"]),
            movieId=int(row["movieId"]),
            tag=row["tag"],
            timestamp=int(row["timestamp"])
        ).__dict__ for row in rows
    ]
    return tags
