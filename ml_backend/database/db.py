from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# PostgreSQL connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://phishguard_user:phishguard_pass_123@localhost:5432/phishguard_db")

# Create engine with connection pooling for concurrent access
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Test connections before using
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── Database Models ─────────────────────────────────────────────────────

class Scan(Base):
    """Store phishing scan records"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_type = Column(String(20))  # "URL", "Email", or "Both"
    target = Column(String(255))    # URL or email content
    score = Column(Float)           # Risk score 0-100
    label = Column(String(20))      # "phishing" or "legitimate"
    is_phishing = Column(Boolean)   # True/False
    created_at = Column(DateTime, default=datetime.now)

# ── Initialize Database ────────────────────────────────────────────────

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

# ── Scan Operations ────────────────────────────────────────────────────

def save_scan(scan_type: str, target: str, score: float, label: str, is_phishing: bool):
    """Save a scan result to database"""
    db = SessionLocal()
    try:
        scan = Scan(
            scan_type=scan_type,
            target=target,
            score=score,
            label=label,
            is_phishing=is_phishing,
            created_at=datetime.now()
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan
    except Exception as e:
        db.rollback()
        print(f"Error saving scan: {e}")
        return None
    finally:
        db.close()

def get_dashboard_stats():
    """Get dashboard statistics"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff_24h = now - timedelta(hours=24)
        
        # ── 24-hour stats ──
        scans_24h = db.query(Scan).filter(Scan.created_at >= cutoff_24h).all()
        email_checks_24h = sum(1 for s in scans_24h if s.scan_type in ["Email", "Both"])
        url_checks_24h = sum(1 for s in scans_24h if s.scan_type in ["URL", "Both"])
        threats_blocked_24h = sum(1 for s in scans_24h if s.is_phishing)
        
        # ── Model accuracy (Static value as requested) ──
        model_accuracy = 94.6
        
        # ── 7-day trend (day by day) ──
        trend_data = {}
        for day_offset in range(7):
            day = now - timedelta(days=day_offset)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_scans = db.query(Scan).filter(
                Scan.created_at >= day_start,
                Scan.created_at < day_end,
                Scan.is_phishing == True
            ).all()
            
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day.weekday()]
            trend_data[day_name] = len(day_scans)
        
        # ── Reverse trend to show oldest first (array of counts only) ──
        trend_list = list(trend_data.items())
        trend_list.reverse()
        trend_list = [count for day, count in trend_list]
        
        # ── Recent Checks ──
        recent_scans = db.query(Scan).order_by(Scan.id.desc()).limit(5).all()
        recent_checks = [
            {
                "type": s.scan_type,
                "target": s.target,
                "riskScore": f"{int(s.score)}/100",
                "status": "blocked" if s.label == "phishing" else "clean"
            }
            for s in recent_scans
        ]

        # ── Detection distribution (clean vs suspicious) ──
        total_scans = len(scans_24h)
        clean_count = sum(1 for s in scans_24h if not s.is_phishing)
        clean_percentage = round((clean_count / total_scans) * 100) if total_scans > 0 else 100
        
        # ── Notes for dashboard ──
        note_email = f"{email_checks_24h} emails scanned in last 24h"
        note_url = f"{url_checks_24h} URLs scanned in last 24h"
        note_threats = f"{threats_blocked_24h} threats detected"
        note_accuracy = f"Based on {total_scans} total scans"
        
        return {
            "emailChecks24h": email_checks_24h,
            "urlChecks24h": url_checks_24h,
            "threatsBlocked24h": threats_blocked_24h,
            "modelAccuracy": model_accuracy,
            "cleanPct": clean_percentage,
            "trend": trend_list,
            "threatScans24h": total_scans,
            "recentChecks": recent_checks,
            "highRiskEmails24h": sum(1 for s in scans_24h if s.is_phishing and s.scan_type in ["Email", "Both"]),
            "suspiciousUrlsFlagged24h": sum(1 for s in scans_24h if s.is_phishing and s.scan_type in ["URL", "Both"]),
            "avgResponseMinutes": 1,
            "noteEmail": note_email,
            "noteUrl": note_url,
            "noteThreats": note_threats,
            "noteAccuracy": note_accuracy
        }
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {}
    finally:
        db.close()

# ── Health check ────────────────────────────────────────────────────

def test_connection():
    """Test database connection"""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
    finally:
        db.close()