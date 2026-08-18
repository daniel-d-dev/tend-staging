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
| Docker | any | Runs PostgreSQL — recommended over installing Postgres natively, see below |
| ffmpeg | any | Required by Whisper for audio decoding |
| Ollama | any | Runs the local Llama 3.2 model used by the group coordinator |

Install ffmpeg on macOS with Homebrew:
```bash
brew install ffmpeg
```

Install Ollama from [ollama.com](https://ollama.com), then pull the exact model the coordinator calls:
```bash
ollama pull llama3.2:3b
```

## Quick start: the database

The recommended setup uses Docker for PostgreSQL only, and runs the API directly with `uvicorn` (steps 2–5 below), so code changes are picked up immediately without a rebuild.

```bash
docker compose up -d db
```

This starts PostgreSQL at `localhost:5432` (data persisted in a Docker volume), with the `tend_staging` database created automatically.

To stop it:
```bash
docker compose down
```

> **Note:** `docker compose up` on its own (without specifying `db`) will also build and start the API container, and it does work, but it has no hot-reload and won't pick up code changes without a full rebuild (`docker compose up --build`). It's not recommended for active development — the steps below, running the API with `uvicorn` directly, are the intended path.

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
DATABASE_URL=postgresql://postgres@localhost:5432/tend_staging
JWT_SECRET=your-secret-key-here

# Optional — these have defaults
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Optional — raises HuggingFace's rate limit for model downloads, not required to run the app
HF_TOKEN=
```

If you're using the Docker database from the previous step, this connection string works as-is — no password, and no manual database creation, `tend_staging` is created automatically the first time the container starts.

If you're running PostgreSQL natively instead, replace the connection string with your own credentials, and create the database yourself:

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

**Start the web app**

From the repository root, in a separate terminal:

```bash
npm run dev
```

This runs Turborepo's `dev` task, which starts the web app at `http://localhost:3000`. It only starts the web app — the mobile app has no `dev` script defined, so Turbo skips it, start it separately below.

**Start the mobile app**

```bash
cd apps/mobile
npm run start
```

Equivalent to `npx expo start`. Then press `a` for Android emulator, `i` for iOS simulator, or scan the QR code with Expo Go on a physical device. The Expo dev server runs at `http://localhost:8081`.

> **Note:** Push notifications require a development build and do not work in Expo Go.

## Other useful commands

| Command | Description |
|---------|-------------|
| `npm run build` | Build the web app for production (the only workspace with a `build` script) |
| `npm run lint` | Lint the web app (the only workspace with a `lint` script) |
| `npm run check-types` | Type-check the web app (the only workspace with a `check-types` script) |
| `npm run format` | Format all files with Prettier, including mobile — this one runs directly across the whole repo, not per-workspace |

## Background jobs

The API runs several scheduled background tasks automatically:

| Time (UTC) | Task |
|------------|------|
| Midnight | Nightly sentiment inference — checks for distress patterns |
| 9:00 AM | Push notification delivery |
| 11:00 AM | Group coordinator — posts a contextual message to each group's feed, if its cooldown allows |

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

**Group coordinator messages never appear, no error shown**

The coordinator uses a local Llama 3.2 model served through Ollama. If Ollama isn't running, the job fails silently and nothing is logged, nothing posts. Make sure Ollama is running (`ollama serve`) and the model is pulled (`ollama pull llama3.2:3b`) before expecting coordinator posts to appear.

**Port already in use**

- API default port: 8000
- Web default port: 3000
- Mobile Expo port: 8081

Kill any process using those ports before starting.
