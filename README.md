# Crypto Funding Arbitrage Terminal

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=flat&logo=react&logoColor=%2361DAFB)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=flat&logo=django&logoColor=white)

A full-stack high-frequency trading dashboard designed to identify and execute arbitrage opportunities based on funding rates across multiple cryptocurrency exchanges. The system aggregates real-time order book data via WebSockets, calculates spreads, and visualizes market depth.

## Key Features

* **Real-time Data Streaming:** Aggregates live Order Book data (L2) from Binance, Bybit, Kucoin, Bitget, CoinEx, Paradex, and Hyperliquid.
* **Arbitrage Scanner:** Automatically identifies "Best Opportunities" for Long/Short funding rate arbitrage strategies.
* **Interactive Dashboard:**
    * Live Order Book visualization with spread calculation.
    * Real-time Candle Charts.
    * Funding Rate comparison tables with filtering and sorting.
* **Robust Backend Architecture:**
    * **Django Channels (ASGI)** for handling WebSocket connections with the frontend.
    * **Redis Pub/Sub** for low-latency data broadcasting between workers and the API.
    * **Celery & Celery Beat** for periodic background tasks and data synchronization.
* **Containerized Deployment:** Fully Dockerized setup with Nginx as a reverse proxy/gateway.

## Tech Stack

### Backend
* **Language:** Python 3.11
* **Framework:** Django 5, Django REST Framework (DRF)
* **Async/WebSockets:** Django Channels, Daphne, Aiohttp
* **Task Queue:** Celery, Redis
* **Database:** PostgreSQL

### Frontend
* **Library:** React 18
* **State Management:** React Context API
* **Networking:** Axios, Native WebSockets
* **Styling:** Bootstrap 5, Custom CSS

### Infrastructure
* **Containerization:** Docker, Docker Compose
* **Gateway:** Nginx (Reverse Proxy for API & WS)
* **OS:** Ubuntu Linux (Production)

## Architecture

The system is built as a set of micro-services orchestrated by Docker Compose:

1.  **Frontend (Nginx):** Serves the React SPA and proxies `/api` and `/ws` requests to the backend.
2.  **Web (Django/Daphne):** Handles HTTP API requests and manages WebSocket connections using Django Channels.
3.  **Market Streamer:** A standalone Python worker running an infinite asyncio loop. It connects to external Exchange WebSockets, normalizes data, and pushes updates to Redis.
4.  **Worker (Celery):** Handles heavy background tasks.
5.  **Redis:** Acts as a Channel Layer for WebSockets and a message broker for Celery.
6.  **PostgreSQL:** Persists user data, historical stats, and trade configurations.

## API Endpoints

The application exposes a RESTful API powered by **Django REST Framework**.
All API routes are prefixed with `/api/`.

**Authentication:** Uses JWT (JSON Web Tokens). Protected endpoints require the header:
`Authorization: Bearer <access_token>`

### Authentication & User

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/register/` | Register a new user account | ❌ |
| `POST` | `/api/token/` | Obtain JWT pair (Login) | ❌ |
| `POST` | `/api/token/refresh/` | Refresh access token | ❌ |
| `GET` | `/api/profile/` | Get current user profile information | ✅ |
| `POST` | `/api/favorite/toggle/` | Add/Remove a symbol from favorites | ✅ |

### Market Data (Scanner)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/funding-table/` | Get aggregated funding rates across exchanges | ❌ |
| `GET` | `/api/best-opportunities/` | Get top arbitrage opportunities (Long/Short) | ❌ |
| `GET` | `/api/coin-detail/<symbol>/` | Get specific details for a coin | ❌ |
| `GET` | `/api/stats/` | General system statistics | ❌ |

### Exchange Keys & Agents

Used for managing API keys and generating signing agents for DEXs (Hyperliquid, Paradex).

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET/POST`| `/api/keys/credentials/` | List or add exchange API credentials | ✅ |
| `POST` | `/api/keys/hl-generate/` | Generate Hyperliquid API Agent | ✅ |
| `POST` | `/api/keys/hl-approve/` | Approve Hyperliquid Agent | ✅ |
| `POST` | `/api/keys/paradex-generate/`| Generate Paradex API Agent | ✅ |
| `POST` | `/api/keys/paradex-approve/` | Approve Paradex Agent | ✅ |

### Trading & Positions

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/positions/` | List active arbitrage positions | ✅ |
| `POST` | `/api/positions/<id>/close/` | Execute close orders for a position | ✅ |

### Proxy Services

Helper endpoints to bypass CORS or fetch specific exchange tokens for the frontend.

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/proxy/kline/` | Proxy exchange candle/OHLCV data | ❌ |
| `GET` | `/api/proxy/kucoin-token/` | Fetch dynamic token for Kucoin WebSocket | ❌ |

## Installation

### Prerequisites
* Docker & Docker Compose installed.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Redocer-kl/FundingRateWebBackend.git](https://github.com/Redocer-kl/FundingRateWebBackend.git)
    cd FundingRateWebBackend
    ```

2.  **Create an `.env` file** in the root directory:
    ```env
    COMPOSE_PROJECT_NAME=trading_bot

    # Django Settings
    DEBUG=False
    SECRET_KEY=your_super_secret_key
    ALLOWED_HOSTS=localhost,127.0.0.1,your-server-ip

    # Database
    POSTGRES_DB=funding_db
    POSTGRES_USER=funding_user
    POSTGRES_PASSWORD=secure_password
    DB_HOST=db
    DB_PORT=5432

    # Redis
    REDIS_URL=redis://redis:6379/0

    # Celery
    CELERY_CONCURRENCY=4
    CELERY_MAX_TASKS_PER_CHILD=100

    #Cryptography
    EXCHANGE_ENCRYPTION_KEY=your_super_secret_key
    ```

3.  **Build and Run:**
    ```bash
    docker compose up -d --build
    ```

4.  **Access the application:**
    Open your browser and navigate to `http://localhost` (or your server IP).

## Usage

1.  **Dashboard:** Select a trading pair to view the live Order Book and Charts.
2.  **Funding Table:** Analyze current funding rates across supported exchanges to find the highest spread.
3.  **Strategy Execution:** Use the "Execute" panel to simulate entry/exit points for Long/Short positions.

## Project Structure

```text
.
├── docker-compose.yml       # Orchestration config
├── funding_project/         # Backend (Django) source
│   ├── scanner/             # Core trading logic app
│   ├── funding_project/     # Project settings (ASGI/WSGI)
│   ├── entrypoint.sh        # Container startup script
│   └── Dockerfile           # Backend image definition
└── scanner-frontend/        # Frontend (React) source
    ├── src/                 # React components & pages
    ├── nginx/               # Nginx configuration
    └── Dockerfile           # Frontend image definition
