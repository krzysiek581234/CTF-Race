from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str

    points: int = Field(default=0)
    activation_code: str = Field(unique=True, index=True)
    code_redeemed: bool = Field(default=False)

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str
    price: int
    secret_text: str

from sqlalchemy import UniqueConstraint
class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    product_id: int = Field(foreign_key="product.id")
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)