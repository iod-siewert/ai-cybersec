# sec-llm-agents – WordPress LLM security scanner

Lokalny skaner bezpieczeństwa kodu (WordPress/PHP/JS) oparty o modele LLM.  
Wykrywa m.in. SQLi, RCE, SSRF, secrets, path traversal, brak nonce, XSS.

## Wymagania

- Python 3.11+
- `OPENAI_API_KEY` w zmiennej środowiskowej
- (opcjonalnie) Docker + docker-compose

## Instalacja

git clone <twoje-repo> sec-llm-agents
cd sec-llm-agents
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python test_wp.py

## Skanowanie pluginu

python cli/repo_scan.py https://github.com/wp-plugins/akismet --max-files 20 --output summary
python cli/repo_scan.py https://github.com/wp-plugins/akismet --max-files 20 --output sarif > akismet.sarif

## Docker

docker compose up -d
docker compose exec scanner python cli/repo_scan.py https://github.com/wp-plugins/akismet
