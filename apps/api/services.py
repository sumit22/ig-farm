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

    def extract_profile(self) -> Optional[Dict]:
        """Extract profile data from Instagram page."""
        try:
            # Extract username from URL
            username_match = re.search(r"instagram\.com/([^/?]+)", self.url)
            if not username_match:
                return None

            username = username_match.group(1)

            # Try to find JSON data in script tags (Instagram loads data in JSON)
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

    def _extract_display_name(self) -> Optional[str]:
        # Look for header with name
        header = self.soup.find("h1")
        return header.text if header else None

    def _extract_bio(self) -> Optional[str]:
        # Look for bio in meta or content sections
        bio_elem = self.soup.find("h2")
        return bio_elem.text if bio_elem else None

    def _extract_followers(self) -> int:
        # Look for follower count
        text = self.soup.get_text()
        match = re.search(r"(\d+(?:,\d+)*)\s*followers?", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0

    def _extract_following(self) -> int:
        # Look for following count
        text = self.soup.get_text()
        match = re.search(r"(\d+(?:,\d+)*)\s*following", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0

    def _extract_posts_count(self) -> int:
        # Look for post count
        text = self.soup.get_text()
        match = re.search(r"(\d+(?:,\d+)*)\s*posts?", text, re.IGNORECASE)
        if match:
            return int(match.group(1).replace(",", ""))
        return 0

    def _extract_verification(self) -> bool:
        # Look for verified badge
        return "verified" in self.html.lower() or "verified_badge" in self.html.lower()

    def _extract_website(self) -> Optional[str]:
        # Look for website link
        link = self.soup.find("a", href=re.compile(r"^https?://"))
        return link["href"] if link else None

    def _extract_profile_image(self) -> Optional[str]:
        # Look for profile image
        img = self.soup.find("img", alt=re.compile(r"profile|avatar", re.IGNORECASE))
        return img.get("src") if img else None

    def extract_related_profiles(self) -> List[str]:
        """Extract similar/related profile usernames."""
        usernames = []
        try:
            # Look for profile links
            links = self.soup.find_all("a", href=re.compile(r"instagram\.com/[^/?]+/?$"))
            for link in links[:10]:  # Limit to 10
                href = link["href"]
                match = re.search(r"instagram\.com/([^/?]+)", href)
                if match:
                    username = match.group(1)
                    if username and username != "explore":
                        usernames.append(username)
        except Exception as e:
            print(f"Error extracting related profiles: {e}")

        return list(set(usernames))  # Remove duplicates


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
