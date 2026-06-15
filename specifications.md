# PROJECT SPECIFICATION: Instagram Profile Discovery & Collection System

**Version:** 1.0  
**Author:** Sumit

## Target Environment

- Windows 11
- Chrome / Edge Browser
- Python 3.12
- FastAPI
- PostgreSQL
- Docker

---

## PROJECT GOAL

Build a locally-installed browser extension that automatically collects publicly visible Instagram profile information while browsing Instagram.

### Extension Requirements

The extension should:

1. Activate only on Instagram
2. Capture profile pages
3. Send page snapshots to a local FastAPI backend
4. Receive the next profile to visit
5. Navigate automatically after a randomized delay
6. Build a growing influencer/profile database

The system is intended for research, influencer discovery, relationship mapping, and profile enrichment.

No Chrome Store publication is required.

---

## CORE DESIGN PRINCIPLE

The browser extension must remain extremely thin.

All intelligence must live in the backend.

### Extension Responsibilities

- Capture
- Upload
- Navigate
- Nothing else

Avoid complex DOM parsing in JavaScript whenever possible.

---

## HIGH LEVEL ARCHITECTURE

```text
Instagram
    ↓
Chrome Extension

    ↓

FastAPI API

    ↓

Capture Queue

    ↓

Raw HTML Archive

    ↓

Profile Extraction Engine

    ↓

Relationship Extraction Engine

    ↓

Scoring Engine

    ↓

PostgreSQL

    ↓

Next Profile Selector
```

---

## PHASE 1: MVP

### Capabilities

- Capture profile pages
- Store HTML snapshots
- Extract profile data
- Extract related profiles
- Queue discovered profiles
- Auto navigate

---

## PHASE 2: Enhanced Collection

### Capabilities

- Network response interception
- JSON extraction
- Profile deduplication
- Verification detection
- Influencer scoring

---

## PHASE 3: Influverse Integration

### Capabilities

- Multi-platform collection (YouTube, TikTok, LinkedIn, X/Twitter)
- Unified creator database

---

## EXTENSION REQUIREMENTS

### Manifest Version

Manifest Version: `3`

### Supported Browsers

- Chrome
- Edge

### Installation

- Manual unpacked extension
- No marketplace deployment

---

## EXTENSION RESPONSIBILITIES

Only:

1. Detect profile page
2. Capture page
3. Upload capture
4. Request next profile
5. Navigate

No business logic, parsing logic, or ranking logic.

---

## PROFILE DETECTION

### Valid Profile URLs

```
https://www.instagram.com/username/
```

### Invalid Patterns

```
/reels/
/explore/
/stories/
/accounts/
/direct/
```

Determine profile page using pathname pattern.

---

## PAGE CAPTURE STRATEGY

### Capture Method

```javascript
document.documentElement.outerHTML
```

Store complete page snapshot.

**Do NOT store only specific sections.**

### Reason

Future extraction requirements are unknown. Full snapshots allow reprocessing.

---

## CAPTURE PAYLOAD

### API Endpoint

```http
POST http://localhost:8000/api/capture
```

### Payload Format

```json
{
  "url": "",
  "captured_at": "",
  "html": "",
  "title": ""
}
```

---

## COMPRESSION

### Requirements

Compress HTML before upload.

### Preferred Methods

1. Brotli
2. Gzip

### Goal

Reduce local API traffic.

---

## AUTOMATIC NAVIGATION

### Workflow

```
Capture Current Profile
        ↓
     Upload
        ↓
Receive Next Profile
        ↓
Wait Random Delay
        ↓
    Navigate
```

---

## RANDOMIZATION

### Navigation Delay

- **Minimum:** 3 seconds
- **Maximum:** 8 seconds

### Formula

```javascript
delay = 3000 + Math.random() * 5000;
```

### Long Pause

After every 20-30 profiles, apply long pause: 30-90 seconds

---

## BACKEND REQUIREMENTS

### Technology Stack

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL

### Project Structure

```
backend/
├── app/
│   ├── api/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   ├── workers/
│   └── parsers/
├── main.py
└── requirements.txt
```

---

## API DESIGN

### POST /api/capture

Store page capture.

### Response Format

```json
{
  "status": "ok",
  "next_profile": "https://www.instagram.com/example/"
}
```

Extension immediately uses this URL.

---

## DATABASE DESIGN

### Table: captures

```sql
id              (PRIMARY KEY)
url             (VARCHAR)
html            (TEXT)
captured_at     (TIMESTAMP)
created_at      (TIMESTAMP)
```

**Purpose:** Raw archive. Never modify.

---

### Table: profiles

```sql
id              (PRIMARY KEY)
username        (VARCHAR, UNIQUE)
display_name    (VARCHAR)
bio             (TEXT)
followers       (INTEGER)
following       (INTEGER)
posts_count     (INTEGER)
website         (VARCHAR)
is_verified     (BOOLEAN)
profile_image   (VARCHAR)
priority_score  (INTEGER)
created_at      (TIMESTAMP)
updated_at      (TIMESTAMP)
```

---

### Table: profile_queue

```sql
id              (PRIMARY KEY)
username        (VARCHAR)
priority_score  (INTEGER)
status          (VARCHAR)
queued_at       (TIMESTAMP)
visited_at      (TIMESTAMP)
```

**Status Values:**
- NEW
- VISITED
- FAILED
- SKIPPED

---

### Table: relationships

```sql
id                  (PRIMARY KEY)
source_profile_id   (FOREIGN KEY → profiles)
target_profile_id   (FOREIGN KEY → profiles)
relationship_type   (VARCHAR)
```

**Relationship Types:**
- SIMILAR
- MUTUAL
- FOLLOWER
- FOLLOWING

---

## PROFILE EXTRACTION ENGINE

### Input/Output

- **Input:** Raw HTML
- **Output:** Structured profile

### Fields to Extract

- username
- display name
- followers
- following
- posts
- website
- profile image
- verification status

### Tools

- BeautifulSoup
- lxml

---

## RELATED PROFILE EXTRACTION

### Process

1. Parse "Similar Accounts" section
2. Extract username and profile URL
3. Insert into queue
4. Avoid duplicates

---

## VERIFIED PROFILE DETECTION

### Detection

Detect verified badge in profile.

### Storage

```sql
is_verified = TRUE
```

Verified accounts receive score bonus.

---

## PRIORITY SCORING

### Base Score: 0

| Criteria | Points |
|----------|--------|
| Verified | +100 |
| Followers > 1M | +50 |
| Followers > 100K | +25 |
| Website Present | +10 |
| Business Account | +20 |

### Formula

```python
score = sum(...)
```

Store in: `priority_score`

---

## NEXT PROFILE SELECTION

### Algorithm

```sql
SELECT *
FROM profile_queue
WHERE status='NEW'
ORDER BY priority_score DESC
LIMIT 1;
```

Return highest score profile.

---

## NETWORK INTERCEPTION MODULE

**Phase 2 Feature**

### Implementation

Implement fetch interception.

### Monitor

- fetch
- XMLHttpRequest

### Capture

```json
{
  "endpoint": "",
  "response": {}
}
```

If JSON exists: prefer JSON extraction.  
Fallback to HTML extraction.

---

## DEDUPLICATION

### Unique Key

`username`

### Behavior

If profile exists: Update profile  
Do not create duplicate.

---

## STORAGE POLICY

Store:
- Raw HTML
- Structured profile
- Relationships

**Never delete captures automatically.**

Future parsers may need historical snapshots.

---

## DOCKER ENVIRONMENT

### Services

- postgres
- fastapi
- worker

docker-compose required.

---

## FUTURE WORKER SYSTEM

### Current Architecture

```
Extension
    ↓
FastAPI
    ↓
Database
```

### Future Architecture

```
Extension
    ↓
FastAPI
    ↓
RabbitMQ
    ↓
Worker
    ↓
Database
```

### Worker Types

- HTML Parser
- Relationship Parser
- Scoring Engine

---

## FUTURE INFLUVERSE INTEGRATION

### Multi-Platform Collection

Sources:
- Instagram
- YouTube
- TikTok
- LinkedIn
- X

### Unified Creator Database

```sql
creator
creator_platforms
creator_relationships
```

Instagram collector becomes one ingestion source.

---

## IMPLEMENTATION PLAN

### Step-by-Step

1. Create FastAPI project
2. Create PostgreSQL schema
3. Create SQLAlchemy models
4. Create Alembic migrations
5. Create capture API
6. Create profile parser service
7. Create queue service
8. Create next-profile selector
9. Create Chrome Extension
10. Implement capture upload
11. Implement navigation workflow
12. Implement related-profile extraction
13. Implement scoring engine
14. Implement network interception
15. Create Docker deployment

### Definition of Done

A user opens Instagram → The extension captures the profile → The backend stores raw HTML → Profile information is extracted → Related profiles are discovered → The backend selects the next best profile → The extension navigates automatically → The database continuously grows into a graph of Instagram profiles and relationships.

### Recommended Monorepo Structure

```
project-root/
├── apps/
│   ├── extension/          (Chrome/Edge Extension - TypeScript)
│   ├── api/                (FastAPI Backend)
│   └── worker/             (Async parsing workers)
├── packages/
│   └── shared/             (DTOs and schemas)
├── docker-compose.yml
└── README.md
```

This fits naturally with microservice architecture for local development.
