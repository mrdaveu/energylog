import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from backend.database import engine, get_db, Base
from backend.models import User, Entry

# Get paths relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EnergyTrack")

# Mount frontend static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class EntryCreate(BaseModel):
    timestamp: datetime
    description: Optional[str] = None
    energy: Optional[int] = None

    @model_validator(mode="after")
    def check_at_least_one(self):
        if self.description is None and self.energy is None:
            raise ValueError("At least one of description or energy must be provided")
        if self.energy is not None and (self.energy < 1 or self.energy > 10):
            raise ValueError("Energy must be between 1 and 10")
        return self


class EntryResponse(BaseModel):
    id: int
    timestamp: datetime
    description: Optional[str]
    energy: Optional[int]

    class Config:
        from_attributes = True


@app.get("/")
async def root():
    return RedirectResponse(url="/new")


@app.get("/new")
async def create_new_user(db: Session = Depends(get_db)):
    user = User()
    db.add(user)
    db.commit()
    db.refresh(user)
    return RedirectResponse(url=f"/u/{user.secret_key}")


@app.get("/u/{secret}", response_class=HTMLResponse)
async def get_user_page(secret: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.secret_key == secret).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    with open(FRONTEND_DIR / "index.html", "r") as f:
        html = f.read()
    return HTMLResponse(content=html)


@app.get("/api/u/{secret}/entries", response_model=list[EntryResponse])
async def get_entries(secret: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.secret_key == secret).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    entries = db.query(Entry).filter(Entry.user_id == user.id).order_by(Entry.timestamp.desc()).all()
    return entries


@app.post("/api/u/{secret}/entries", response_model=EntryResponse)
async def create_entry(secret: str, entry: EntryCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.secret_key == secret).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_entry = Entry(
        user_id=user.id,
        timestamp=entry.timestamp,
        description=entry.description,
        energy=entry.energy
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


@app.get("/demo")
async def create_demo_user(db: Session = Depends(get_db)):
    """Create a demo user with pre-populated entries for testing"""
    user = User()
    db.add(user)
    db.commit()
    db.refresh(user)

    now = datetime.utcnow()

    # Demo entries with RELATIVE timestamps (minutes ago from now)
    demo_entries = [
        # Recent entries (within last few hours)
        {"minutes_ago": 5, "description": "Just had coffee", "energy": 6},
        {"minutes_ago": 45, "description": "Woke up, feeling groggy", "energy": 4},
        {"minutes_ago": 120, "description": "Couldn't sleep well", "energy": 3},

        # Yesterday
        {"minutes_ago": 180, "description": "Late night snack - crackers", "energy": None},
        {"minutes_ago": 300, "description": "Gaming session", "energy": 5},
        {"minutes_ago": 420, "description": "Dinner - pasta with pesto", "energy": None},
        {"minutes_ago": 540, "description": "Afternoon walk", "energy": 7},
        {"minutes_ago": 600, "description": "Lunch - sandwich", "energy": None},
        {"minutes_ago": 720, "description": "Morning meeting, tired", "energy": 4},
        {"minutes_ago": 840, "description": "Breakfast - oatmeal", "energy": 6},

        # Two days ago
        {"minutes_ago": 1500, "description": "McDonalds - 9 chicken mcnuggets", "energy": None},
        {"minutes_ago": 1515, "description": "Extreme fatigue(!), brain turning off", "energy": 2},
        {"minutes_ago": 1700, "description": "Cheese bagel with chicken", "energy": None},
        {"minutes_ago": 1800, "description": "Greek yogurt, mango, pecans", "energy": 7},

        # Three days ago
        {"minutes_ago": 2880, "description": "Sleep 9h, difficult to wake up", "energy": 4},
        {"minutes_ago": 3000, "description": "Bagel with scrambled eggs", "energy": None},
        {"minutes_ago": 3200, "description": "Indomie with veggies", "energy": None},
        {"minutes_ago": 3400, "description": "Focused work session", "energy": 9},

        # Four days ago
        {"minutes_ago": 4320, "description": "Woke up, black coffee", "energy": 5},
        {"minutes_ago": 4500, "description": "Pho for lunch", "energy": None},
        {"minutes_ago": 4680, "description": "Afternoon slump", "energy": 3},
        {"minutes_ago": 4800, "description": "Evening cooking", "energy": 6},
        {"minutes_ago": 5000, "description": "Late night reading", "energy": 5},

        # Five days ago
        {"minutes_ago": 5760, "description": "Oatmeal with blueberries", "energy": 6},
        {"minutes_ago": 5900, "description": "Green tea, reading", "energy": 7},
        {"minutes_ago": 6100, "description": "Leftover pasta", "energy": None},
        {"minutes_ago": 6300, "description": "Walk in the park", "energy": 7},
        {"minutes_ago": 6500, "description": "Salmon dinner", "energy": None},

        # Six days ago
        {"minutes_ago": 7200, "description": "Slept in, croissant", "energy": 6},
        {"minutes_ago": 7400, "description": "Ramen for lunch", "energy": None},
        {"minutes_ago": 7600, "description": "Vitamin D supplement", "energy": None},
        {"minutes_ago": 7800, "description": "Stir fry tofu", "energy": None},
        {"minutes_ago": 8000, "description": "Late night coding", "energy": 4},

        # Seven days ago
        {"minutes_ago": 8640, "description": "Eggs and toast", "energy": 7},
        {"minutes_ago": 8800, "description": "Burrito bowl", "energy": None},
        {"minutes_ago": 9000, "description": "Post-lunch crash", "energy": 3},
        {"minutes_ago": 9200, "description": "Espresso pick-me-up", "energy": 6},
        {"minutes_ago": 9400, "description": "Light dinner, soup", "energy": None},
    ]

    for entry_data in demo_entries:
        timestamp = now - timedelta(minutes=entry_data["minutes_ago"])
        entry = Entry(
            user_id=user.id,
            timestamp=timestamp,
            description=entry_data["description"],
            energy=entry_data.get("energy")
        )
        db.add(entry)

    db.commit()
    return RedirectResponse(url=f"/u/{user.secret_key}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
