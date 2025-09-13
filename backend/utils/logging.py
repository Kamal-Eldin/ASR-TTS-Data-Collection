from logging import getLogger, StreamHandler, FileHandler, Formatter, DEBUG

logger= getLogger(name="app-logger")
logger.setLevel(DEBUG)

log_form= Formatter(fmt="{module}-{levelname}-{message}", style='{')
to_console= StreamHandler()
to_file= FileHandler(filename="/app/logs", mode='a')

to_console.setFormatter(log_form)
to_file.setFormatter(log_form)

logger.addHandler(to_console)
logger.addHandler(to_file)


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