"""
SQLAlchemy database setup and models.
"""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session


SQLITE_DATABASE_URL = "sqlite:///./data/colending.db"

engine = create_engine(
    SQLITE_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Partner(Base):
    """Partners table - stores lender/originator information"""
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # 'YUBI', 'EXTERNAL', 'OWN_BOOK'
    active = Column(Boolean, default=True)

    partnerships_as_originator = relationship("Partnership", foreign_keys="[Partnership.orig_id]", back_populates="originator")
    partnerships_as_partner = relationship("Partnership", foreign_keys="[Partnership.partner_id]", back_populates="partner")


class Partnership(Base):
    """Partnerships table - stores co-lending arrangements"""
    __tablename__ = "partnerships"

    id = Column(Integer, primary_key=True, index=True)
    orig_id = Column(Integer, ForeignKey("partners.id"))
    partner_id = Column(Integer, ForeignKey("partners.id"))
    min_amount = Column(Float)
    max_amount = Column(Float)
    products = Column(Text)  # JSON array of product types
    rate_formula = Column(Text)  # JSON rate configuration
    monthly_limit = Column(Float)
    service_fee = Column(Float)
    cost_funds = Column(Float)
    active = Column(Boolean, default=True)

    originator = relationship("Partner", foreign_keys=[orig_id], back_populates="partnerships_as_originator")
    partner = relationship("Partner", foreign_keys=[partner_id], back_populates="partnerships_as_partner")
    performance_records = relationship("Performance", back_populates="partnership")
    allocations = relationship("Allocation", back_populates="partnership")


class Program(Base):
    """Programs table - allocation strategy configurations"""
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    orig_id = Column(Integer, ForeignKey("partners.id"))
    name = Column(String, nullable=False)
    product_types = Column(Text)  # JSON array of supported product types
    strategy_config = Column(Text)  # JSON configuration for weights/strategy


class Performance(Base):
    """Historical performance data for partnerships"""
    __tablename__ = "performance"

    id = Column(Integer, primary_key=True, index=True)
    partnership_id = Column(Integer, ForeignKey("partnerships.id"))
    total_apps = Column(Integer)
    approved_apps = Column(Integer)
    month_year = Column(String)  # Format: "YYYY-MM"

    partnership = relationship("Partnership", back_populates="performance_records")


class Allocation(Base):
    """Loan allocation records"""
    __tablename__ = "allocations"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String, nullable=False)
    partnership_id = Column(Integer, ForeignKey("partnerships.id"))
    orig_profit = Column(Float)
    lender_profit = Column(Float)
    blended_rate = Column(Float)
    selection_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    partnership = relationship("Partnership", back_populates="allocations")


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_sample_data():
    """Initialize database with sample data"""
    db = next(get_db())
    
    # Check if data already exists
    if db.query(Partner).first():
        return
    
    # Create sample partners
    yubi = Partner(name="YUBI", type="YUBI", active=True)
    lender_a = Partner(name="Lender A", type="EXTERNAL", active=True)
    lender_b = Partner(name="Lender B", type="EXTERNAL", active=True)
    lender_c = Partner(name="Lender C", type="EXTERNAL", active=True)
    
    db.add_all([yubi, lender_a, lender_b, lender_c])
    db.commit()
    
    # Create sample partnerships
    partnership_a = Partnership(
        orig_id=yubi.id,
        partner_id=lender_a.id,
        min_amount=50000,
        max_amount=10000000,
        products=json.dumps(["PERSONAL_LOAN", "BUSINESS_LOAN"]),
        rate_formula=json.dumps({"participation": 0.25}),
        monthly_limit=50000000,
        service_fee=0.018,
        cost_funds=0.085,
        active=True
    )
    
    partnership_b = Partnership(
        orig_id=yubi.id,
        partner_id=lender_b.id,
        min_amount=50000,
        max_amount=10000000,
        products=json.dumps(["PERSONAL_LOAN"]),
        rate_formula=json.dumps({"participation": 0.30}),
        monthly_limit=40000000,
        service_fee=0.020,
        cost_funds=0.088,
        active=True
    )
    
    partnership_c = Partnership(
        orig_id=yubi.id,
        partner_id=lender_c.id,
        min_amount=50000,
        max_amount=5000000,
        products=json.dumps(["PERSONAL_LOAN", "BUSINESS_LOAN"]),
        rate_formula=json.dumps({"participation": 0.35}),
        monthly_limit=30000000,
        service_fee=0.022,
        cost_funds=0.090,
        active=True
    )
    
    db.add_all([partnership_a, partnership_b, partnership_c])
    db.commit()
    
    # Create sample program
    program = Program(
        orig_id=yubi.id,
        name="Default Co-lending Program",
        product_types=json.dumps(["PERSONAL_LOAN", "BUSINESS_LOAN"]),
        strategy_config=json.dumps({"strategy": "weighted_random"})
    )
    
    db.add(program)
    db.commit()
    
    # Create sample performance data
    performance_data = [
        Performance(partnership_id=partnership_a.id, total_apps=1000, approved_apps=850, month_year="2024-08"),
        Performance(partnership_id=partnership_a.id, total_apps=1200, approved_apps=1020, month_year="2024-07"),
        Performance(partnership_id=partnership_b.id, total_apps=800, approved_apps=576, month_year="2024-08"),
        Performance(partnership_id=partnership_b.id, total_apps=900, approved_apps=648, month_year="2024-07"),
        Performance(partnership_id=partnership_c.id, total_apps=600, approved_apps=348, month_year="2024-08"),
        Performance(partnership_id=partnership_c.id, total_apps=650, approved_apps=377, month_year="2024-07"),
    ]
    
    db.add_all(performance_data)
    db.commit()
    db.close()