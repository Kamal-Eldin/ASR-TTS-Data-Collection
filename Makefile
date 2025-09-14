.SILENT:
create_project:
	curl -X POST -d "id=1&project_name=new_from_container&prompts_text=firstexample&is_rtl=false&created_at=2025-09-12" http://localhost:8500/create_project/


deploy:
	echo "placing env vars from template into root"
	echo "----------------------------------------------"
	cp ./.env.template ./.env
	echo "disabling running compose components"
	echo "----------------------------------------------"
	docker compose down
	echo "building system components"
	echo "----------------------------------------------"
	docker compose build
	echo "deploying container services and network..watch mode enabled for frontend & backend"
	echo "----------------------------------------------"
	docker compose up -w