## CareerPilot Agent Monorepo

Welcome! This repo is a monorepo scaffold for the CareerPilot AI agent system.

—

Next steps (copy/paste and run locally when ready):

1) Initialize git and branches
   - git init
   - git add . && git commit -m "chore: initial monorepo scaffold"
   - git branch -M main
   - git checkout -b dev

2) Install frontend dependencies
   - cd frontend
   - npm install
   - npm run dev

3) Create and activate backend venv, then install deps
   - cd backend
   - python3 -m venv .venv && source .venv/bin/activate
   - pip install -r requirements.txt
   - uvicorn app.main:app --reload

4) Open two terminals to run frontend and backend concurrently.

5) Create feature branches off `dev` for new work, e.g. `feat/resume-upload`.

—

### Repository name

`careerpilot-agent`

### Structure

```
careerpilot-agent/
  frontend/   # Next.js + TypeScript + Tailwind
  backend/    # FastAPI + Python
  .gitignore
  README.md
  COMMIT_MESSAGE.txt
```

### Tech stack

- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: FastAPI (Python), Uvicorn

### Branching model

- `main`: Protected, release-ready. Only merge via PR from `dev`.
- `dev`: Integration branch. Feature branches merge here after review.
- Feature branches: `feat/<short-description>` (e.g., `feat/resume-upload`).
- Bugfix/hotfix branches: `fix/<short-description>` or `hotfix/<short-description>`.

Recommended rules:
- Require PR reviews before merging to `dev` and `main`.
- Use squash merges for feature branches.
- Keep `main` deployable at all times.

### Conventional commits (suggested)

- `feat:` new feature
- `fix:` bug fix
- `chore:` tooling, configs, minor updates
- `docs:` documentation only
- `refactor:` code change that neither fixes a bug nor adds a feature
- `test:` add or update tests

### Frontend (Next.js + TypeScript + Tailwind)

- Located in `frontend/`
- Includes minimal config files to bootstrap a standard Next.js + Tailwind stack.

Dev commands (after `npm install`):
- `npm run dev`: start dev server
- `npm run build`: build for production
- `npm run start`: start production server

### Backend (FastAPI)

- Located in `backend/`
- Minimal FastAPI app with `/health` route.

Dev commands (after venv + install):
- `uvicorn app.main:app --reload`

### Environments and secrets

- Do not commit secrets. Use `.env` files locally; keep real secrets in a secure vault.
- Example environment files:
  - `backend/.env.example`

### CI/CD (future work)

- Add GitHub Actions for lint/test/build for both frontend and backend.
- Add deploy workflows targeting your infrastructure (Vercel, AWS, etc.).

### Licensing

Add a license suited to your project goals (MIT, Apache-2.0, etc.).


