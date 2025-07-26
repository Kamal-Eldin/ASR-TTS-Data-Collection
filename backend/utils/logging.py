def log_interaction(action: str, data: dict):
    """Log user interactions (currently just prints to console)"""
    # TODO: Implement proper logging to database
    # with session_lock:
    #     db = SessionLocal()
    #     try:
    #         interaction = Interaction(action=action, data=data)
    #         db.add(interaction)
    #         db.commit()
    #     finally:
    #         db.close()
    print(f"🔄 Logging interaction: {action} with data: {data}") 