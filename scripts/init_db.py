from core.db import engine
from core.models import Base

def main():
    print("⚠️ Dropping all tables...")
    Base.metadata.drop_all(bind=engine)

    print("🛠 Creating all tables...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database schema initialized.")

if __name__ == "__main__":
    main()
