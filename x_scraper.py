from email.mime import text
from playwright.sync_api import sync_playwright
import pandas as pd
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

USERNAME = "ShivamaniG34885"
PASSWORD = "Shivamani@26"

def login_to_x(page):
    print("🔐 Logging in...")
    page.goto("https://x.com/login", wait_until="networkidle", timeout=60000)

    # Fill username/email
    page.wait_for_selector("input[name='text']", timeout=15000)
    page.fill("input[name='text']", USERNAME)
    page.keyboard.press("Enter")
    page.wait_for_timeout(3000)

    # If redirected to homepage, skip password step
    if "home" in page.url:
        print("✅ Already logged in (redirected to home)")
        return

    # If it asks for password
    if page.locator("input[name='password']").count() > 0:
        page.fill("input[name='password']", PASSWORD)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)
    else:
        print("⚠️ Password input not found. Possibly already logged in or unexpected flow.")

def scrape_top3_x_tweets(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        login_to_x(page)

        # Now go to target profile
        print("📄 Navigating to target profile...")
        page.goto(url, wait_until='load', timeout=60000)

        print("⏳ Waiting for timeline content to load...")
        for i in range(5):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(3000)

        # Scroll to load tweets
        for i in range(6):
            if page.locator("article[role='article']").count() >= 3:
                break
            print(f"🔄 Scrolling... attempt {i+1}")
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2500)

        # Extract tweets
        articles = page.locator("article[role='article']")
        if articles.count() == 0:
            print("❌ No tweets found.")
            browser.close()
            return pd.DataFrame(columns=["Tweet Text", "Tweet URL"])

        tweet_data = []
        for tweet in articles.all():
            # Stop after 3 collected tweets
            if len(tweet_data) >= 3:
                break
            try:
                # Skip pinned tweet or non-content tweets
                if "Pinned Tweet" in tweet.inner_text():
                    continue
                if tweet.locator("div[data-testid='tweetText']").count() == 0:
                    continue

                text = tweet.locator("div[data-testid='tweetText']").inner_text(timeout=5000)
                url_suffix = tweet.locator("a[role='link']").last.get_attribute("href")
                full_url = f"https://x.com{url_suffix}" if url_suffix else "N/A"

                tweet_data.append((text.strip(), full_url))
            except Exception as e:
                print(f"⚠️ Skipping tweet: {e}")
                continue

        browser.close()
        return pd.DataFrame(tweet_data, columns=["Tweet Text", "Tweet URL"])

def summarize_tweet(text):
    prompt = f"Summarize this tweet. If it is a new publication, include the publication title and the conference name. If it is another type of post, provide only the main gist. Do not include any hashtags. Only return the core content:\n\n{text}"
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error summarizing tweet: {e}")
        return "Summary failed"
    
def store_in_mongodb(dataframe):
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB")
    collection_name = os.getenv("MONGO_COLLECTION")

    try:
        client = MongoClient(mongo_uri)
        db = client[db_name]
        collection = db[collection_name]

        # Convert each row to a dictionary and insert
        records = dataframe.to_dict(orient='records')
        result = collection.insert_many(records)
        print(f"✅ Stored {len(result.inserted_ids)} tweets in MongoDB.")
    except Exception as e:
        print(f"❌ Failed to store in MongoDB: {e}")
    
def main():
    url = "https://x.com/NGCN_Group"
    df = scrape_top3_x_tweets(url)
    if df.empty:
        print("❌ No tweets extracted.")
        return
    
    df['Summary'] = df['Tweet Text'].apply(summarize_tweet)

    print("\nSummaries:")
    print(df[['Tweet Text', 'Summary', 'Tweet URL']].to_string(index=False))

    # Store in MongoDB
    store_in_mongodb(df)

    
if __name__ == "__main__":
    main()
