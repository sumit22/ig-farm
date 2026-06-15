from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os

from models import engine, Base, Capture, Profile, ProfileQueue, init_db
from schemas import CaptureRequest, CaptureResponse, NextProfileResponse
from services import ProfileParser, QueueService, ProfileSelector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logger = logging.getLogger('ig-farm-api')

# Initialize database
init_db()

app = FastAPI(title="IG Farm API", version="1.0")

# Allow CORS so extension and browser preflight requests succeed during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    logger.info('Health check requested')
    return {"status": "ok"}


@app.post("/api/capture", response_model=CaptureResponse)
def capture(payload: CaptureRequest, db: Session = Depends(get_db)):
    """
    Receive page capture from extension.
    Store raw HTML.
    Extract profile data.
    Return next profile to visit.
    """
    logger.info('Capture endpoint hit: %s', payload.url)
    logger.debug('Capture payload title=%s captured_at=%s html_length=%d', payload.title, payload.captured_at, len(payload.html or ''))
    try:
        # Store raw capture
        capture = Capture(
            url=payload.url,
            html=payload.html,
            title=payload.title,
            captured_at=payload.captured_at,
        )
        db.add(capture)
        db.flush()

        # Extract username from URL to mark as visited
        import re
        username_match = re.search(r"instagram\.com/([^/?]+)", payload.url)
        visited_username = username_match.group(1) if username_match else None

        # Extract profile data from HTML
        parser = ProfileParser(payload.html, payload.url)
        profile_data = parser.extract_profile()

        if profile_data:
            # Check if profile exists
            existing = db.query(Profile).filter_by(username=profile_data["username"]).first()
            if existing:
                # Update
                for key, value in profile_data.items():
                    if value is not None:
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
            else:
                # Create new
                profile = Profile(**profile_data)
                db.add(profile)
                db.flush()

            # Extract related profiles
            related = parser.extract_related_profiles()
            if related:
                queue_service = QueueService(db)
                for username in related:
                    queue_service.add_to_queue(username)

            # Mark the captured profile as VISITED in queue
            if visited_username:
                queue_item = db.query(ProfileQueue).filter_by(username=visited_username).first()
                if queue_item:
                    queue_item.status = "VISITED"
                    queue_item.visited_at = datetime.utcnow()

        db.commit()

        # Get next profile
        selector = ProfileSelector(db)
        next_profile_url = selector.get_next_profile()
        logger.info('Capture processed, next_profile=%s', next_profile_url)

        return CaptureResponse(
            status="ok",
            next_profile=next_profile_url or "https://www.instagram.com/explore/",
        )

    except Exception as e:
        db.rollback()
        logger.exception('Capture processing failed')
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/next-profile", response_model=NextProfileResponse)
def get_next_profile(db: Session = Depends(get_db)):
    """
    Get next profile from queue.
    """
    selector = ProfileSelector(db)
    next_profile = selector.get_next_profile()

    return NextProfileResponse(
        next_profile=next_profile or "https://www.instagram.com/explore/"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
