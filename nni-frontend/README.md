# nni-frontend

React/Vite frontend for Natural Number Interpretation.

For the simplest local setup, run `./start.sh` from the project root. To run the frontend independently:

```bash
npm ci
npm run dev
```

The development proxy forwards `/api` requests to the FastAPI backend. Set `VITE_BACKEND_URL` when the backend runs on a non-default port.
