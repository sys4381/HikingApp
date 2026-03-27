from database import engine, Base
import models

def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully! You can now re-ingest the GPX files.")

if __name__ == "__main__":
    reset_database()
