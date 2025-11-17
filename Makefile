include .env.template

.SILENT:
create_project:
	curl -X POST -d "id=1&project_name=$(project_name)&prompts_text=$(prompts)&is_rtl=false" http://localhost:8500/create_project/

deploy:
	echo "--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--."
	echo "placing env vars from project.conf into compose .env file"
	cp ./project.conf ./.env
	echo "--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--."
# 	echo "stopping running services"
# 	docker compose down
# 	echo "--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--.--."
	echo "deploying compose services and network..watch mode enabled for frontend & backend directories"
	docker compose up --build --no-deps --force-recreate -w