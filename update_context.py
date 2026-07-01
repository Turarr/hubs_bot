import os
import requests
import chromadb
import sys

def main():
    try:
        access_token = os.environ.get("ACCESS_TOKEN")
        if not access_token:
            raise ValueError("ACCESS_TOKEN is missing in environment variables.")

        # 1. Fetching biography and username
        me_url = f"https://graph.instagram.com/v25.0/me?fields=biography,username&access_token={access_token}"
        me_res = requests.get(me_url).json()
        if "error" in me_res:
            raise Exception(f"Error fetching profile: {me_res['error']}")
        
        # 2. Fetching last 10 posts
        media_url = f"https://graph.instagram.com/v25.0/me/media?fields=caption,timestamp&limit=10&access_token={access_token}"
        media_res = requests.get(media_url).json()
        if "error" in media_res:
            raise Exception(f"Error fetching media: {media_res['error']}")

        posts = media_res.get("data", [])
        print(f"Fetched {len(posts)} posts.")

        # 3. Connecting to ChromaDB
        client = chromadb.PersistentClient(path="/data/chroma_db")
        
        try:
            client.delete_collection("instagram_context")
        except Exception:
            pass
        
        collection = client.create_collection("instagram_context")
        docs_added = 0

        bio = me_res.get("biography")
        if bio:
            collection.add(
                ids=["bio"],
                documents=[bio],
                metadatas=[{"type": "bio"}]
            )
            docs_added += 1

        for i, post in enumerate(posts):
            caption = post.get("caption")
            if caption:
                collection.add(
                    ids=[f"post_{i}"],
                    documents=[caption],
                    metadatas=[{"type": "post", "timestamp": post.get("timestamp")}]
                )
                docs_added += 1

        print(f"Added {docs_added} documents.")
        print("Context updated successfully.")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
