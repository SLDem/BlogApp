from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel, EmailStr, constr
from passlib.context import CryptContext
import jwt
import datetime
from cachetools import TTLCache

app = FastAPI()

DATABASE_URL = "mysql+mysqlconnector://user:password@localhost/dbname"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

cache = TTLCache(maxsize=100, ttl=300)

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)


# Models
class User(Base):
    """User model."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Post(Base):
    """Post model."""
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class UserCreate(BaseModel):
    """Base model for creating users."""
    email: EmailStr
    password: constr(min_length=6)


class UserLogin(BaseModel):
    """Base model for logging in users."""
    email: EmailStr
    password: str


class PostCreate(BaseModel):
    """Base model for creating posts."""
    text: str


def get_db():
    """Get db session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_password_hash(password: str) -> str:
    """Get hashed password."""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password) -> bool:
    """Verify password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict) -> str:
    """Create a JWT token."""
    e = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    e.update({"exp": expire})
    return jwt.encode(e, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify a JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user and save in db."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}


@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Get token to use in requests."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_token({"sub": db_user.email})
    return {"token": token}


@app.post("/addpost")
def add_post(post: PostCreate, token: str, db: Session = Depends(get_db)):
    """Create a new post"""
    t = verify_token(token)
    user = db.query(User).filter(User.email == t["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if len(post.text.encode("utf-8")) > 1048576:
        raise HTTPException(status_code=400, detail="Post too large")
    p = Post(text=post.text, user_id=user.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"postID": p.id}


@app.get("/getposts")
def get_posts(token: str, db: Session = Depends(get_db)):
    """Get user posts."""
    t = verify_token(token)
    user = db.query(User).filter(User.email == t["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if user.email in cache:
        return cache[user.email]
    p = db.query(Post).filter(Post.user_id == user.id).all()
    cache[user.email] = p
    return p


@app.delete("/deletepost")
def delete_post(postID: int, token: str, db: Session = Depends(get_db)):
    """Delete a post from db."""
    t = verify_token(token)
    user = db.query(User).filter(User.email == t["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    post = db.query(Post).filter(Post.id == postID, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}
