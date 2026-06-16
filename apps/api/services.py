from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from datetime import datetime
import re
from typing import Dict, List, Optional

from models import Profile, ProfileQueue, Relationship


class ProfileParser:
    def __init__(self, html: str, url: str):
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, "html.parser")
        self._json_data = None

    def extract_profile(self) -> Optional[Dict]:
        """Extract profile data from Instagram page."""
        try:
            username_match = re.search(r"instagram\.com/([^/?]+)", self.url)
            if not username_match:
                return None

            username = username_match.group(1)

            profile_data = {
                "username": username,
                "display_name": self._extract_display_name(),
                "bio": self._extract_bio(),
                "followers": self._extract_followers(),
                "following": self._extract_following(),
                "posts_count": self._extract_posts_count(),
                "is_verified": self._extract_verification(),
                "website": self._extract_website(),
                "profile_image": self._extract_profile_image(),
            }

            return profile_data
        except Exception as e:
            print(f"Error extracting profile: {e}")
            return None

    def _extract_json_data(self) -> Optional[dict]:
        if self._json_data is not None:
            return self._json_data

        scripts = self.soup.find_all("script")
        for script in scripts:
            if not script.string:
                continue

            text = script.string.strip()
            if text.startswith("window._sharedData"):
                match = re.search(r"window\._sharedData\s*=\s*({.*});", text, re.S)
                if match:
                    try:
                        self._json_data = __import__("json").loads(match.group(1))
                        return self._json_data
                    except Exception:
                        continue

            if text.startswith("{") and "graphql" in text:
                try:
                    candidate = __import__("json").loads(text)
                    self._json_data = candidate
                    return self._json_data
                except Exception:
                    continue

        ld_json = self.soup.find("script", type="application/ld+json")
        if ld_json and ld_json.string:
            try:
                self._json_data = __import__("json").loads(ld_json.string)
                return self._json_data
            except Exception:
                pass

        return None

    def _parse_number(self, value) -> int:
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)

        text = str(value).strip().lower().replace(",", "")
        try:
            if text.endswith("m"):
                return int(float(text[:-1]) * 1_000_000)
            if text.endswith("k"):
                return int(float(text[:-1]) * 1_000)
            return int(float(text))
        except ValueError:
            match = re.search(r"(\d+)\s*followers?", text)
            if match:
                return int(match.group(1))
            return 0

    def _extract_display_name(self) -> Optional[str]:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user:
                return user.get("full_name") or user.get("name")

        header = self.soup.find("h1")
        return header.text.strip() if header else None

    def _extract_bio(self) -> Optional[str]:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user:
                return user.get("biography") or user.get("description")

        bio_elem = self.soup.find("h2")
        return bio_elem.text.strip() if bio_elem else None

    def _extract_followers(self) -> int:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user:
                count = user.get("edge_followed_by", {}).get("count") or user.get("followers")
                if count is not None:
                    return self._parse_number(count)

        if text := self._extract_meta_description():
            match = re.search(r"([\d\.kKmM,]+)\s+followers", text)
            if match:
                return self._parse_number(match.group(1))

        text = self.soup.get_text()
        match = re.search(r"([\d,]+)\s*followers?", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0

    def _extract_following(self) -> int:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user:
                count = user.get("edge_follow", {}).get("count") or user.get("following")
                if count is not None:
                    return self._parse_number(count)

        if text := self._extract_meta_description():
            match = re.search(r"([\d\.kKmM,]+)\s+following", text)
            if match:
                return self._parse_number(match.group(1))

        text = self.soup.get_text()
        match = re.search(r"([\d,]+)\s*following", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0

    def _extract_posts_count(self) -> int:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user:
                count = user.get("edge_owner_to_timeline_media", {}).get("count") or user.get("posts")
                if count is not None:
                    return self._parse_number(count)

        if text := self._extract_meta_description():
            match = re.search(r"([\d\.kKmM,]+)\s+posts", text)
            if match:
                return self._parse_number(match.group(1))

        text = self.soup.get_text()
        match = re.search(r"([\d,]+)\s*posts?", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0

    def _extract_verification(self) -> bool:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user is not None:
                return bool(user.get("is_verified") or user.get("verified"))
        return "verified" in self.html.lower() or "verified_badge" in self.html.lower()

    def _extract_website(self) -> Optional[str]:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user:
                return user.get("external_url")

        link = self.soup.find("a", href=re.compile(r"^https?://"))
        return link["href"] if link else None

    def _extract_profile_image(self) -> Optional[str]:
        if data := self._extract_json_data():
            user = self._find_user_node(data)
            if user:
                return user.get("profile_pic_url_hd") or user.get("profile_pic_url")

        img = self.soup.find("img", alt=re.compile(r"profile|avatar", re.IGNORECASE))
        return img.get("src") if img else None

    def _extract_meta_description(self) -> Optional[str]:
        description = self.soup.find("meta", attrs={"property": "og:description"})
        if description and description.get("content"):
            return description.get("content")
        name_desc = self.soup.find("meta", attrs={"name": "description"})
        if name_desc and name_desc.get("content"):
            return name_desc.get("content")
        return None

    def _find_user_node(self, data: dict) -> Optional[dict]:
        if not data:
            return None

        if isinstance(data, dict):
            if "entry_data" in data:
                profile_page = data.get("entry_data", {}).get("ProfilePage")
                if profile_page and isinstance(profile_page, list):
                    user = profile_page[0].get("graphql", {}).get("user")
                    if user:
                        return user

            if "graphql" in data and "user" in data["graphql"]:
                return data["graphql"]["user"]

            if "user" in data:
                return data["user"]

        return None

    def extract_related_profiles(self) -> List[str]:
        """Extract similar/related profile usernames from the similar accounts section."""
        usernames = set()
        try:
            labels = [
                r"Similar accounts",
                r"Suggested for you",
                r"Suggested",
                r"Recommended",
                r"Suggestions",
            ]
            label_regex = re.compile(r"(?:%s)" % r"|".join(labels), re.IGNORECASE)

            sections = []
            for node in self.soup.find_all(text=label_regex):
                parent = node.parent
                while parent and parent.name not in ["section", "div", "article", "main"]:
                    parent = parent.parent
                if parent is not None:
                    sections.append(parent)

            if not sections:
                sections = self.soup.find_all(
                    lambda tag: tag.name in ["section", "div", "article"]
                    and tag.get_text(" ").strip() and label_regex.search(tag.get_text(" "))
                )

            for section in sections:
                links = section.find_all("a", href=re.compile(r"instagram\.com/[^/?]+/?$"))
                for link in links:
                    href = link.get("href", "")
                    match = re.search(r"instagram\.com/([^/?]+)", href)
                    if match:
                        username = match.group(1)
                        if username and username not in ["explore", "reels", "stories", "accounts", "direct"]:
                            if username != self._current_username():
                                usernames.add(username)

            if not usernames:
                # fallback: if no similar section found, try any profile-like links in page body
                links = self.soup.find_all("a", href=re.compile(r"instagram\.com/[^/?]+/?$"))
                for link in links:
                    href = link.get("href", "")
                    match = re.search(r"instagram\.com/([^/?]+)", href)
                    if match:
                        username = match.group(1)
                        if username and username not in ["explore", "reels", "stories", "accounts", "direct"]:
                            if username != self._current_username():
                                usernames.add(username)

        except Exception as e:
            print(f"Error extracting related profiles: {e}")

        return list(usernames)

    def _current_username(self) -> Optional[str]:
        match = re.search(r"instagram\.com/([^/?]+)", self.url)
        return match.group(1) if match else None


class QueueService:
    def __init__(self, db: Session):
        self.db = db

    def add_to_queue(self, username: str, priority_score: int = 0):
        """Add profile to queue, avoid duplicates."""
        existing = self.db.query(ProfileQueue).filter_by(username=username).first()
        if not existing:
            queue_item = ProfileQueue(
                username=username, priority_score=priority_score, status="NEW"
            )
            self.db.add(queue_item)
            self.db.commit()

    def mark_visited(self, username: str):
        """Mark profile as visited."""
        item = self.db.query(ProfileQueue).filter_by(username=username).first()
        if item:
            item.status = "VISITED"
            item.visited_at = datetime.utcnow()
            self.db.commit()


class ProfileSelector:
    def __init__(self, db: Session):
        self.db = db

    def get_next_profile(self) -> Optional[str]:
        """Get highest priority profile from queue."""
        item = (
            self.db.query(ProfileQueue)
            .filter_by(status="NEW")
            .order_by(ProfileQueue.priority_score.desc())
            .first()
        )

        if item:
            return f"https://www.instagram.com/{item.username}/"

        return None

    def update_profile_scores(self):
        """Calculate and update priority scores for profiles."""
        profiles = self.db.query(Profile).all()

        for profile in profiles:
            score = 0

            if profile.is_verified:
                score += 100

            if profile.followers > 1000000:
                score += 50
            elif profile.followers > 100000:
                score += 25

            if profile.website:
                score += 10

            profile.priority_score = score

        self.db.commit()
