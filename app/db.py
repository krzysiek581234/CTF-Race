from sqlmodel import SQLModel, create_engine, Session, select
from pathlib import Path
from typing import Generator
from .models import Product

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(DATABASE_URL, echo=False)

def init_db() -> None:
    """Create tables and seed initial products."""
    SQLModel.metadata.create_all(engine)
    seed_products()

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

# ---- seed products ----
def seed_products() -> None:
    with Session(engine) as session:
        exists = session.exec(select(Product)).first()
        if exists:
            return
        session.add_all([
            Product(
                name="Flaga",
                description="Tylko dla najlepszych wyjadaczy",
                price=100,
                secret_text="FLAG{Szybkość_i_Precyzja}"
            ),
            Product(
                name="Darmowa wskazówka",
                description="Może się przydać, ale nie musi",
                price=10,
                secret_text="HINT{Sprawdź_logi_serwera}"
            ),
        ])
        session.commit()
