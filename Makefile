create_project:
	curl -X POST -d "id=1&project_name=new_from_container&prompts_text=firstexample&is_rtl=false&created_at=2025-09-12" http://localhost:8100/create_project/