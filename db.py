from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# --- Config DB ---
DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Modele ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    medical_profile = relationship(
        "MedicalProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete"
    )

class MedicalProfile(Base):
    __tablename__ = "medical_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Date generale
    varsta = Column(Integer)
    inaltime = Column(Float)
    greutate = Column(Float)
    grupa_sange = Column(String)
    rh = Column(String)

    # Istoric obstetrical
    nr_sarcini = Column(Integer)
    nr_nasteri = Column(Integer)
    tip_nasteri = Column(String)
    avorturi = Column(Integer)
    dum = Column(String)
    dpn = Column(String)

    # Sarcina curentă
    complicatii = Column(String)
    sarcina_risc = Column(Boolean, default=False)

    # Afecțiuni
    boli = Column(String)

    # Medicație și alergii
    medicatie_sarcina = Column(String)
    alergii = Column(String)

    # Stil de viață
    fumatoare = Column(Boolean, default=False)
    alcool = Column(Boolean, default=False)

    user = relationship("User", back_populates="medical_profile")

# --- Funcții helper ---
def create_db():
    Base.metadata.create_all(bind=engine)
    print("Baza de date a fost creată!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
