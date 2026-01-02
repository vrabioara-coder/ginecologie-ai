from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


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
    inaltime = Column(Integer)
    greutate = Column(Integer)
    grupa_sange = Column(String)
    rh = Column(String)

    # Istoric obstetrical
    nr_sarcini = Column(Integer)
    nr_nasteri = Column(Integer)
    tip_nasteri = Column(String)
    avorturi = Column(String)  # spontane / la cerere
    dum = Column(String)       # Data ultimei menstruatii
    dpn = Column(String)       # Data probabila a nasterii

    # Sarcina curenta
    complicatii = Column(String)
    sarcina_risc = Column(Boolean, default=False)

    # Afecțiuni
    boli = Column(String)

    # Medicație
    medicatie_sarcina = Column(String)
    alergii = Column(String)

    # Stil de viață
    fumatoare = Column(Boolean, default=False)
    alcool = Column(Boolean, default=False)

    user = relationship("User", back_populates="medical_profile")


def create_db():
    Base.metadata.create_all(bind=engine)
