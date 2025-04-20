from core.db import Base, engine
import core.models

def init_db():
    Base.metadata.drop_all(bind=engine) # delete
    Base.metadata.create_all(bind=engine) # create
    print("✅ Database schema initialized.")

if __name__ == "__main__":
    init_db()