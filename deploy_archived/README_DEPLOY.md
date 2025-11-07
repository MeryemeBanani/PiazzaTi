Deploy notes — automated steps added by assistant

What I changed
- The GitHub Actions workflows (`.github/workflows/deploy.yml` and `ci.yml`) now build the frontend, create a tarball (`frontend_dist.tgz`) and SCP it to the server at `/tmp` during deployment. The remote deploy extracts the archive into `/var/www/piazzati` and installs an nginx snippet `piazzati_parse_grafana_home.conf` if uploaded.
- The backend Dockerfile now installs Poppler and Tesseract in the final image so OCR works inside the container.
- The systemd unit `deploy/piazzati-backend.service` was cleaned to a single entry that runs the backend as user `piazzati`.
- A small helper script `scripts/check_ocr_env.sh` was added to verify presence of `pdftoppm` and `tesseract`.

How deployment works now (summary)
1. Push to `main` (or trigger the deploy workflow manually).
2. The runner builds the frontend (`npm ci && npm run build`) and packs `dist` into `frontend_dist.tgz`.
3. The runner SCPs the archive and `deploy/nginx_piazzati_parse_grafana_home.conf` and `deploy/home.html` to the server's `/tmp`.
4. The remote SSH deploy extracts the frontend into `/var/www/piazzati`, moves the nginx conf to `/etc/nginx/conf.d/` and reloads nginx (best-effort).
5. The remote deploy updates the repo, pulls the backend image, and runs `docker compose up -d --build`.

Notes & next steps
- The deploy creates a minimal `backend/.env` containing `OLLAMA_MODEL_NAME` if `backend/.env.scaleway` is not present in the repo; you should provide production secrets properly (either add `backend/.env.scaleway` on the server or update the workflow to generate a complete `.env` from GitHub Secrets securely).
- If your server does not allow SSH as `root`, change the SSH user in the workflows to an account with the necessary permissions and that can run the required commands (or can use `sudo` without a password). Update the secrets accordingly.
- If you prefer the frontend to be served from a different location or by a container, adjust the install steps accordingly.

Rollback
- If anything goes wrong, you can revert the last deploy by checking out the previous commit on the server and restarting services, or use the docker compose logs to inspect failures.
