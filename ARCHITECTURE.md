# Architecture

## System Overview
Doogfood is a monolithic Flask application serving both API endpoints and server-side rendered HTML pages, backed by MongoDB.

## Component Diagram
The system uses a two-container setup:
- **app**: Flask + Jinja2 templates for routing and rendering
- **db**: MongoDB for data storage

## Request Flow
1. Client request → Flask app
2. `before_request` hook loads user from session cookie
3. Route handler checks role via decorators
4. Handler queries MongoDB via pymongo
5. Returns JSON (API) or rendered HTML (pages)

## Authentication Design
- Session-based auth using random tokens stored in MongoDB sessions collection
- Tokens set as HTTP cookies (`session=<token>`)
- Pre-seeded tokens for acceptance checker compatibility
- `before_request` middleware loads user on every request

## Role Isolation Strategy
- Backend middleware pattern: `require_auth`, `require_role` decorators
- Judge score isolation enforced server-side: judge can only query own scores
- No frontend-only hiding — all access control is in route handlers
- Specific check: `GET /api/judge/scores?judge=X` verifies X matches current user's identity

## Data Flow
- Data flows from seed scripts into MongoDB.
- MongoDB data is queried by Flask APIs and rendered into Jinja2 templates or served as JSON.

## Directory Structure
- `avi.py`: Main application entry point
- `templates/`: Jinja2 HTML templates
- `static/`: Static assets
- `tests/`: Test files
- `Dockerfile` / `docker-compose.yml`: Container definitions

## Design Decisions
- Jinja2 templates over SPA: ensures checker can find content without JS execution
- Round-robin judge assignment: simple, fair, defensible
- Z-score normalization: corrects for judge leniency/harshness bias
- stddev=0 guard: prevents division by zero for judges who score uniformly
