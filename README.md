# Tend

An AI-driven peer support app for friend groups. Tend monitors daily check-ins, detects emotional distress using NLP sentiment analysis, and nudges designated friends when someone may need support.

## Project structure

This is a Turborepo monorepo with three apps and two shared packages:

```
tend-staging/
├── apps/
│   ├── api/        # FastAPI backend (Python)
│   ├── web/        # Next.js web frontend
│   └── mobile/     # React Native (Expo) mobile app
├── packages/
│   ├── ui/                  # Shared UI components
│   ├── eslint-config/       # Shared ESLint config
│   └── typescript-config/   # Shared TypeScript config
├── turbo.json
└── package.json
```

## Prerequisites

Install all of the following before proceeding:

| Tool | Version | Purpose |
|------|---------|---------|
| Node.js | >= 18 | Web and mobile apps |
| npm | >= 11 | Package manager (ships with Node) |
| Python | 3.13 | FastAPI backend |
| PostgreSQL | >= 14 | Database |
| ffmpeg | any | Required by Whisper for audio decoding |

Install ffmpeg on macOS with Homebrew:
```bash
brew install ffmpeg
```

## Quick start with Docker

If you have [Docker](https://www.docker.com/get-started) installed, you can run the API and database with a single command from the repository root:

```bash
docker compose up
```

This starts:
- The FastAPI API at `http://localhost:8000`
- A PostgreSQL database (data persisted in a Docker volume)

To run in the background:
```bash
docker compose up -d
```

To stop:
```bash
docker compose down
```

The web and mobile apps still need to be run locally — see steps 1 and 4–5 below.

> **Note:** The first build will take a while as Docker installs Python dependencies including torch and Whisper.

---

## 1. Clone and install JavaScript dependencies

From the repository root, install all workspace dependencies in one command:

```bash
npm install
```

This installs dependencies for the web app, mobile app, and all shared packages via npm workspaces.

## 2. Set up the Python backend

Create a virtual environment:

```bash
cd apps/api
python -m venv venv
```

Activate the virtual environment:
- macOS / Linux: `source venv/bin/activate`
- Windows (PowerShell): `venv\Scripts\Activate.ps1`
- Windows (Command Prompt): `venv\Scripts\activate.bat`

Install Python dependencies:

```bash
pip install -r requirements.txt
```

> **Note:** `torch`, `transformers`, and `openai-whisper` are large packages (several GB). The first install will take a while. The app also downloads the HuggingFace model `j-hartmann/emotion-english-distilroberta-base` and the Whisper base model on first startup.

## 3. Configure environment variables

Create a `.env` file inside `apps/api/`:

```env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/tend_staging
JWT_SECRET=your-secret-key-here

# Optional — these have defaults
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Replace `your_user` and `your_password` with your PostgreSQL credentials.

Create the PostgreSQL database:

```sql
CREATE DATABASE tend_staging;
```

The API automatically creates all tables on startup — no manual migrations needed.

## 4. Configure the mobile app API URL

The mobile app connects to the backend using a local IP address. This file is not committed to the repository, so you need to create it manually:

```bash
# apps/mobile/constants/api.ts
export const API_URL = "http://<your-local-ip>:8000";
```

Find your local IP with `ifconfig` (macOS/Linux) or `ipconfig` (Windows). Your phone and development machine must be on the same network.

The web app is pre-configured to use `http://localhost:8000` and does not need changes.

## 5. Running the apps

**Start the FastAPI backend**

In a dedicated terminal, with the virtual environment active:

```bash
cd apps/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The `--host 0.0.0.0` flag is required for physical device testing. The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API documentation.

**Start the web and mobile apps (via Turbo)**

From the repository root, in a separate terminal:

```bash
npm run dev
```

This uses Turborepo to start all JavaScript apps in parallel:
- Web app: `http://localhost:3000`
- Mobile app: Expo dev server at `http://localhost:8081` (scan the QR code with the Expo Go app)

> **Note:** Push notifications require a development build and do not work in Expo Go.

**Start apps individually (optional)**

Web only:
```bash
cd apps/web
npm run dev
```

Mobile only:
```bash
cd apps/mobile
npm run start
```

Then press `a` for Android emulator, `i` for iOS simulator, or scan the QR code with Expo Go on a physical device.

## Other useful commands

| Command | Description |
|---------|-------------|
| `npm run build` | Build all apps for production |
| `npm run lint` | Lint all TypeScript/JavaScript apps |
| `npm run check-types` | Type-check all apps |
| `npm run format` | Format all files with Prettier |

## Background jobs

The API runs several scheduled background tasks automatically:

| Time (UTC) | Task |
|------------|------|
| Midnight | Nightly sentiment inference — checks for distress patterns |
| 9:00 AM | Push notification delivery |
| 10:00 AM | Post-nudge evaluation — checks if sentiment improved |

These start automatically when the API starts. No extra configuration is needed.

## Common issues

**psycopg2 install fails**

Try installing the binary version directly:
```bash
pip install psycopg2-binary
```

**Expo Go cannot reach the API**

Make sure your phone and computer are on the same Wi-Fi network, and that the IP in `apps/mobile/constants/api.ts` matches your machine's current local IP.

**HuggingFace model download is slow**

The `j-hartmann/emotion-english-distilroberta-base` model downloads automatically on first API startup. Ensure you have a stable internet connection for the first run.

**Port already in use**

- API default port: 8000
- Web default port: 3000
- Mobile Expo port: 8081

Kill any process using those ports before starting.
