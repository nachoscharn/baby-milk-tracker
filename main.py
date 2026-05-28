from baby_milk_tracker.cli import run_menu
from baby_milk_tracker.database import init_db

if __name__ == "__main__":
    init_db()
    run_menu()
