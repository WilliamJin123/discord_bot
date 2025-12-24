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
        env_base_url = os.getenv("REDDIT_BASE_URL")
        self.base_url = (env_base_url or base_url).rstrip("/")
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
        base_urls = [self.base_url]
        if self.base_url != "https://old.reddit.com":
            base_urls.append("https://old.reddit.com")

        last_error: Optional[Exception] = None
        for base_url in base_urls:
            url = f"{base_url}{clean_path}"
            try:
                response = requests.get(
                    url,
                    headers=self._headers(),
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                last_error = exc
                status = getattr(exc.response, "status_code", None)
                if status in (403, 429):
                    continue
                raise
            except requests.RequestException as exc:
                last_error = exc
                raise
        if last_error:
            raise last_error
        return {}

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
        try:
            response = self.get(path, params=params)
        except requests.RequestException:
            return []
        children = response.get("data", {}).get("children", [])
        gems = []
        for child in children:
            data = child.get("data", {})
            image_url = data.get("url_overridden_by_dest") or data.get("url", "")
            gem = Gem(title=data.get("title", ""), image_url=image_url)
            gems.append(gem)
        return gems
    
    def get_gem(self) -> Optional[Gem]:
        gems = self.get_gems()
        if not gems:
            return None
        return choice(gems)

    async def get_gems_async(self, *args, **kwargs) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_gems, *args, **kwargs)

    async def get_gem_async(self, *args, **kwargs) -> Optional[Gem]:
        return await asyncio.to_thread(self.get_gem, *args, **kwargs)

# testing
# async def main():
#         reddit_client = RedditClient()
#         gem = await reddit_client.get_gem_async()
#         print(gem)

# if __name__ == "__main__":
#     reddit_client = RedditClient()

#     asyncio.run(main())
