include .env.template

.SILENT:
create_project:
	curl -X POST -d "id=1&project_name=$(project_name)&prompts_text=$(prompts)&is_rtl=false" http://localhost:8500/create_project/

update_urls:
	echo "writing BACKEND_URL var from environment to frontend components"
	sed -i "s|const BACKEND_URL.*;|const BACKEND_URL = '${BACKEND_URL}';|" \
		/workspaces/Voice-Dataset-Collection/frontend/src/components/Projects.tsx \
		/workspaces/Voice-Dataset-Collection/frontend/src/components/Recording.tsx \
		/workspaces/Voice-Dataset-Collection/frontend/src/components/Settings.tsx


deploy: update_urls
	echo "--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--."
	echo "placing env vars from template into root"
	cp ./.env.template ./.env
	echo "--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--."
	echo "disabling running compose components"
	docker compose down
	echo "--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--."
	echo "building system components"
	docker compose build
	echo "--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--."
	echo "deploying container services and network..watch mode enabled for frontend & backend"
	docker compose up -w