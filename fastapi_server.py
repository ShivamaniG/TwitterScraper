from fastapi import FastAPI
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

# Load MongoDB credentials
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB", "TwitterScraperDB")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "tweets")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

app = FastAPI(title="Tweet Summary API", version="1.0")

# Optional: CORS if you want to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use ["http://localhost:3000"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/tweets", tags=["Tweets"])
def get_top_3_tweets():
    tweets = list(collection.find({}, {"_id": 0}).limit(3))  # limit to top 3
    return {"count": len(tweets), "tweets": tweets}
