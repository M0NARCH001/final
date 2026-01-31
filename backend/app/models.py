from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


# ---------------- Users ----------------
class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True)   # login id
    password_hash = Column(String)

    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)

    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    target_weight_kg = Column(Float, nullable=True)

    activity_level = Column(String, nullable=True)
    medical_conditions = Column(Text, nullable=True)

    goal = Column(String, nullable=True)   # weight_loss / diabetes / muscle_gain

    # Health conditions for dietary adjustments
    has_diabetes = Column(Boolean, default=False)
    has_hypertension = Column(Boolean, default=False)
    has_pcos = Column(Boolean, default=False)
    muscle_gain_focus = Column(Boolean, default=False)
    heart_health_focus = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())



# ---------------- Food Items ----------------
class FoodItem(Base):
    __tablename__ = "food_items"

    food_id = Column(Integer, primary_key=True, index=True)
    food_name = Column(String, index=True)
    main_name = Column(String, index=True)
    subcategories_json = Column(Text, nullable=True)
    source = Column(String, nullable=True)

    Calories_kcal = Column(Float, nullable=True)
    Carbohydrates_g = Column(Float, nullable=True)
    Protein_g = Column(Float, nullable=True)
    Fats_g = Column(Float, nullable=True)
    FreeSugar_g = Column(Float, nullable=True)
    Fibre_g = Column(Float, nullable=True)
    Sodium_mg = Column(Float, nullable=True)
    Calcium_mg = Column(Float, nullable=True)
    Iron_mg = Column(Float, nullable=True)
    VitaminC_mg = Column(Float, nullable=True)
    Folate_ug = Column(Float, nullable=True)


# ---------------- RDA ----------------
class RDA(Base):
    __tablename__ = "rda"

    rda_id = Column(Integer, primary_key=True, index=True)
    life_stage = Column(String, unique=True, nullable=False)

    Calories_kcal = Column(Float, nullable=True)
    Carbohydrates_g = Column(Float, nullable=True)
    Protein_g = Column(Float, nullable=True)
    Fats_g = Column(Float, nullable=True)
    FreeSugar_g = Column(Float, nullable=True)
    Fibre_g = Column(Float, nullable=True)
    Sodium_mg = Column(Float, nullable=True)
    Calcium_mg = Column(Float, nullable=True)
    Iron_mg = Column(Float, nullable=True)
    VitaminC_mg = Column(Float, nullable=True)
    Folate_ug = Column(Float, nullable=True)


# ---------------- Food Logs ----------------
class FoodLog(Base):
    __tablename__ = "food_log"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=True)

    # IMPORTANT: points to food_items
    food_id = Column(Integer, ForeignKey("food_items.food_id"), nullable=False)

    quantity = Column(Float, default=1.0)
    unit = Column(String, nullable=True)
    cooking_method = Column(String, nullable=True)
    portion_g_cooked = Column(Float, nullable=True)
    logged_at = Column(DateTime, server_default=func.now())


# ---------------- User Goals ----------------
class UserGoal(Base):
    __tablename__ = "user_goal"

    goal_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    rda_id = Column(Integer, ForeignKey("rda.rda_id"), nullable=True)

    nutrient_name = Column(String, nullable=False)
    recommended_value = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


# ---------------- Recommendations ----------------
class Recommendation(Base):
    __tablename__ = "recommendation"

    rec_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=True)
    rec_text = Column(Text, nullable=False)
    rec_type = Column(String, nullable=True)
    rec_score = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
