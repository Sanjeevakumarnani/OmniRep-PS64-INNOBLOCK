from sqlalchemy import create_engine, String, Integer, Float, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime, timezone
from config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass

def utcnow(): return datetime.now(timezone.utc)

class Passport(Base):
    __tablename__ = "passports"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    owner_address: Mapped[str] = mapped_column(String(42), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    score: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    sybil_risk: Mapped[int] = mapped_column(Integer, default=0)
    tier: Mapped[int] = mapped_column(Integer, default=0)
    input_hash: Mapped[str] = mapped_column(String(66), default="")
    links_hash: Mapped[str] = mapped_column(String(66), default="")
    model_version: Mapped[int] = mapped_column(Integer, default=10001)
    version: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_sync_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    published_tx_hash: Mapped[str] = mapped_column(String(80), default="")
    published_chain: Mapped[str] = mapped_column(String(40), default="ethereum-sepolia")
    generic_metrics: Mapped[str] = mapped_column(Text, default="{}")

class AuthChallenge(Base):
    __tablename__ = "auth_challenges"
    nonce: Mapped[str] = mapped_column(String(120), primary_key=True)
    passport_id: Mapped[str] = mapped_column(String(80), index=True)
    address: Mapped[str] = mapped_column(String(42), index=True)
    chain_id: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[int] = mapped_column(Integer, index=True)

class WalletLink(Base):
    __tablename__ = "wallet_links"
    __table_args__ = (
        UniqueConstraint("passport_id", "address", "chain_id", name="uq_wallet_passport_address_chain"),
        Index("ix_wallet_passport_status", "passport_id", "status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passport_id: Mapped[str] = mapped_column(String(80), index=True)
    address: Mapped[str] = mapped_column(String(42), index=True)
    chain_id: Mapped[int] = mapped_column(Integer)
    signature: Mapped[str] = mapped_column(Text)
    nonce: Mapped[str] = mapped_column(String(120))
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="verified")

class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        Index("ix_activity_passport_timestamp", "passport_id", "timestamp"),
        Index("ix_activity_passport_type", "passport_id", "activity_type"),
    )
    id: Mapped[str] = mapped_column(String(140), primary_key=True)
    passport_id: Mapped[str] = mapped_column(String(80), index=True)
    chain_id: Mapped[int] = mapped_column(Integer)
    chain_name: Mapped[str] = mapped_column(String(60))
    address: Mapped[str] = mapped_column(String(42), index=True)
    tx_hash: Mapped[str] = mapped_column(String(80))
    block_number: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[int] = mapped_column(Integer)
    activity_type: Mapped[str] = mapped_column(String(60))
    source: Mapped[str] = mapped_column(String(80))
    contract_address: Mapped[str] = mapped_column(String(42))
    normalized_amount: Mapped[float] = mapped_column(Float, default=0)
    quality_grade: Mapped[str] = mapped_column(String(1), default="C")
    details: Mapped[str] = mapped_column(Text, default="{}")

class ScoreRun(Base):
    __tablename__ = "score_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passport_id: Mapped[str] = mapped_column(String(80), index=True)
    score: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[int] = mapped_column(Integer)
    model_version: Mapped[int] = mapped_column(Integer)
    input_hash: Mapped[str] = mapped_column(String(66))
    breakdown_json: Mapped[str] = mapped_column(Text)
    risk_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

def init_db(): Base.metadata.create_all(engine)
