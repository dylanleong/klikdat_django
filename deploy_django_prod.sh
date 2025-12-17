source ~/.bashrc
cd /app/klikdat_django
docker compose down
git stash
git pull
docker compose -f compose.yml -f compose.prod.yml up --build -d
