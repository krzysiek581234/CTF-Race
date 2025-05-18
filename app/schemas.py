from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=128)

class UserRead(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True

class ProductRead(BaseModel):
    id: int
    name: str
    description: str
    price: float

    class Config:
        orm_mode = True
