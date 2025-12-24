from typing import Any, Dict, List, Optional
from random import choice
import asyncio
import requests
from pydantic import BaseModel
import os

class Gem(BaseModel):
    title: str
    image_url: str


class RedditClient:
    def __init__(self, base_url: str = "https://www.reddit.com", timeout: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = os.getenv("REDDIT_USER_AGENT", "desktop:chudbot:1.x (by /u/Next-Average656)")
        self.timeout = timeout

 
    def _headers(self) -> Dict[str, str]:
        """reddit needs a user agent in the header for app identification"""
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """basic GET for any reddit endpoint that doesn't require oauth"""
        clean_path = path if path.startswith("/") else f"/{path}"
        if not clean_path.endswith(".json"):
            clean_path = f"{clean_path}.json"
        url = f"{self.base_url}{clean_path}"
        response = requests.get(
            url,
            headers=self._headers(),
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_gems(
        self,
        subreddit: str = "kitchencels",
        sort: str = "top",
        t: str = "week",
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Return top posts of the week for a subreddit."""
        params: Dict[str, Any] = {
            "t": t,
            "limit": limit,
        }

        path = f"/r/{subreddit}/{sort}"
        response = self.get(path, params=params)
        children = response.get("data", {}).get("children", [])
        gems = []
        for child in children:
            data = child.get("data", {})
            image_url = data.get("url_overridden_by_dest") or data.get("url", "")
            gem = Gem(title=data.get("title", ""), image_url=image_url)
            gems.append(gem)
        return gems
    
    def get_gem(self) -> Gem:
        gems = self.get_gems()
        return choice(gems)

    async def get_gems_async(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_gems, *args, **kwargs)

    async def get_gem_async(self, *args, **kwargs) -> Gem:
        return await asyncio.to_thread(self.get_gem, *args, **kwargs)

# testing
# async def main():
#         reddit_client = RedditClient()
#         gem = await reddit_client.get_gem_async()
#         print(gem)

# if __name__ == "__main__":
#     reddit_client = RedditClient()

#     asyncio.run(main())
