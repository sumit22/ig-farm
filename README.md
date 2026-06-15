# IG Farm - Instagram Profile Discovery System

Collect Instagram profile data with a browser extension and FastAPI backend.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Chrome/Edge Browser
- Python 3.12 (for local development)

### Setup

1. **Start the backend:**

```bash
docker-compose up -d
```

This starts:
- PostgreSQL database on `localhost:5432`
- FastAPI server on `localhost:8000`

2. **Load the Chrome Extension:**

- Open Chrome/Edge
- Go to `chrome://extensions/`
- Enable "Developer mode" (top right)
- Click "Load unpacked"
- Select `apps/extension/` folder

3. **Test the API:**

```bash
curl http://localhost:8000/health
```

## Architecture

```
Instagram
    ↓
Chrome Extension (capture & upload)
    ↓
FastAPI (store & process)
    ↓
PostgreSQL (database)
    ↓
Profile extraction & scoring
    ↓
Next profile selector
```

## Implementation Status

- [x] FastAPI backend
- [x] PostgreSQL schema
- [x] Capture API endpoint
- [x] Profile extraction engine
- [x] Queue & scoring system
- [x] Chrome extension (basic)
- [ ] Network interception (Phase 2)
- [ ] Worker system (Phase 2)
- [ ] Multi-platform (Phase 3)

## API Endpoints

### POST /api/capture
Receive page capture from extension.

**Request:**
```json
{
  "url": "https://www.instagram.com/username/",
  "captured_at": "2026-06-16T10:00:00",
  "html": "...",
  "title": "Instagram Profile"
}
```

**Response:**
```json
{
  "status": "ok",
  "next_profile": "https://www.instagram.com/next_user/"
}
```

### GET /api/next-profile
Get next profile from queue.

**Response:**
```json
{
  "next_profile": "https://www.instagram.com/username/"
}
```

## Database Tables

- `captures` - Raw HTML snapshots
- `profiles` - Extracted profile data
- `profile_queue` - Profiles to visit
- `relationships` - Profile connections

## Development

### Local Setup

```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

### Check logs:

```bash
docker-compose logs -f api
```

### Stop services:

```bash
docker-compose down
```

## Notes

- Extension runs only on Instagram.com
- Captures full page HTML for future reprocessing
- Auto-navigates with randomized 3-8s delay
- Deduplicates profiles by username
- Scoring prioritizes verified, high-follower accounts

## License

MIT
