from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, timedelta
from uuid import uuid4, UUID

app = FastAPI()

# Data Models


class Magazine(BaseModel):
    id: UUID
    name: str
    description: str
    base_price: float = Field(gt=0, description="Base price must be greater than zero")


class Plan(BaseModel):
    id: UUID
    title: str
    description: str
    renewal_period: int = Field(
        gt=0, description="Renewal period must be greater than zero"
    )
    tier: int
    discount: float = Field(ge=0, le=1, description="Discount must be between 0 and 1")


class Subscription(BaseModel):
    id: UUID
    user_id: UUID
    magazine_id: UUID
    plan_id: UUID
    price: float = Field(gt=0, description="Price must be greater than zero")
    renewal_date: date
    is_active: bool


# In-memory storage for demonstration purposes
magazines = []
plans = []
subscriptions = []


# Seed Plans
def seed_plans():
    global plans
    plans.extend(
        [
            Plan(
                id=uuid4(),
                title="Silver Plan",
                description="Basic plan which renews monthly",
                renewal_period=1,
                tier=1,
                discount=0.0,
            ),
            Plan(
                id=uuid4(),
                title="Gold Plan",
                description="Standard plan which renews every 3 months",
                renewal_period=3,
                tier=2,
                discount=0.05,
            ),
            Plan(
                id=uuid4(),
                title="Platinum Plan",
                description="Premium plan which renews every 6 months",
                renewal_period=6,
                tier=3,
                discount=0.10,
            ),
            Plan(
                id=uuid4(),
                title="Diamond Plan",
                description="Exclusive plan which renews annually",
                renewal_period=12,
                tier=4,
                discount=0.25,
            ),
        ]
    )


seed_plans()

# Endpoints


@app.post("/magazines/", response_model=Magazine)
def create_magazine(magazine: Magazine):
    magazines.append(magazine)
    return magazine


@app.get("/magazines/", response_model=List[Magazine])
def list_magazines():
    return magazines


@app.get("/plans/", response_model=List[Plan])
def list_plans():
    return plans


@app.post("/subscriptions/", response_model=Subscription)
def create_subscription(user_id: UUID, magazine_id: UUID, plan_id: UUID):
    magazine = next((m for m in magazines if m.id == magazine_id), None)
    plan = next((p for p in plans if p.id == plan_id), None)

    if not magazine:
        raise HTTPException(status_code=404, detail="Magazine not found")
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    active_sub = next(
        (
            s
            for s in subscriptions
            if s.user_id == user_id and s.magazine_id == magazine_id and s.is_active
        ),
        None,
    )
    if active_sub:
        raise HTTPException(
            status_code=400,
            detail="Active subscription already exists for this magazine",
        )

    price = magazine.base_price * (1 - plan.discount)
    renewal_date = date.today() + timedelta(days=plan.renewal_period * 30)

    subscription = Subscription(
        id=uuid4(),
        user_id=user_id,
        magazine_id=magazine_id,
        plan_id=plan_id,
        price=price,
        renewal_date=renewal_date,
        is_active=True,
    )
    subscriptions.append(subscription)
    return subscription


@app.get("/subscriptions/", response_model=List[Subscription])
def list_subscriptions(user_id: UUID):
    return [s for s in subscriptions if s.user_id == user_id and s.is_active]


@app.put("/subscriptions/{subscription_id}", response_model=Subscription)
def modify_subscription(subscription_id: UUID, plan_id: UUID):
    subscription = next(
        (s for s in subscriptions if s.id == subscription_id and s.is_active), None
    )
    plan = next((p for p in plans if p.id == plan_id), None)

    if not subscription:
        raise HTTPException(status_code=404, detail="Active subscription not found")
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    subscription.is_active = False

    magazine = next((m for m in magazines if m.id == subscription.magazine_id), None)
    price = magazine.base_price * (1 - plan.discount)
    renewal_date = date.today() + timedelta(days=plan.renewal_period * 30)

    new_subscription = Subscription(
        id=uuid4(),
        user_id=subscription.user_id,
        magazine_id=subscription.magazine_id,
        plan_id=plan_id,
        price=price,
        renewal_date=renewal_date,
        is_active=True,
    )
    subscriptions.append(new_subscription)
    return new_subscription


@app.delete("/subscriptions/{subscription_id}", response_model=Subscription)
def cancel_subscription(subscription_id: UUID):
    subscription = next(
        (s for s in subscriptions if s.id == subscription_id and s.is_active), None
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="Active subscription not found")

    subscription.is_active = False
    return subscription
