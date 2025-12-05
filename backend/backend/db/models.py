from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    business_user_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    accesses = relationship("Access", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")

    __table_args__ = (UniqueConstraint("user_id", "role_id", name="_user_role_uc"),)


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    accesses = relationship("Access", back_populates="application", cascade="all, delete-orphan")
    managers = relationship("AppManagerMap", back_populates="application", cascade="all, delete-orphan")
    owners = relationship("AppOwnerMap", back_populates="application", cascade="all, delete-orphan")
    bos = relationship("BusinessOwnerMap", back_populates="application", cascade="all, delete-orphan")


class AppManagerMap(Base):
    __tablename__ = "app_manager_map"
    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    application = relationship("Application", back_populates="managers")


class AppOwnerMap(Base):
    __tablename__ = "app_owner_map"
    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    application = relationship("Application", back_populates="owners")


class BusinessOwnerMap(Base):
    __tablename__ = "business_owner_map"
    id = Column(Integer, primary_key=True)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    application = relationship("Application", back_populates="bos")


class ReportingMap(Base):
    __tablename__ = "reporting_map"
    id = Column(Integer, primary_key=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    __table_args__ = (UniqueConstraint("manager_id", "user_id", name="_manager_user_uc"),)


class ReportingAppMap(Base):
    __tablename__ = "reporting_app_map"
    id = Column(Integer, primary_key=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    app_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    __table_args__ = (UniqueConstraint("manager_id", "app_id", name="_rm_app_uc"),)


class Access(Base):
    __tablename__ = "access"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="accesses")
    application = relationship("Application", back_populates="accesses")


class ReviewCycle(Base):
    __tablename__ = "review_cycle"
    id = Column(Integer, primary_key=True)
    quarter = Column(String, nullable=False)
    status = Column(String, default="in_progress")
    created_at = Column(DateTime, default=datetime.utcnow)


class ReviewItem(Base):
    __tablename__ = "review_item"
    id = Column(Integer, primary_key=True)
    cycle_id = Column(Integer, ForeignKey("review_cycle.id"), nullable=False)
    access_id = Column(Integer, ForeignKey("access.id"), nullable=False)

    reporting_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    app_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    app_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    business_owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    pending_stage = Column(String, nullable=False, default="reporting_manager")

    manager_action = Column(String, nullable=True)
    manager_comment = Column(Text, nullable=True)
    manager_timestamp = Column(DateTime, nullable=True)

    application_manager_action = Column(String, nullable=True)
    application_manager_comment = Column(Text, nullable=True)
    application_manager_timestamp = Column(DateTime, nullable=True)

    application_owner_action = Column(String, nullable=True)
    application_owner_comment = Column(Text, nullable=True)
    application_owner_timestamp = Column(DateTime, nullable=True)

    business_owner_action = Column(String, nullable=True)
    business_owner_comment = Column(Text, nullable=True)
    business_owner_timestamp = Column(DateTime, nullable=True)

    final_status = Column(String, nullable=True)


class StagingChange(Base):
    __tablename__ = "staging_change"
    id = Column(Integer, primary_key=True)
    review_item_id = Column(Integer, ForeignKey("review_item.id"), nullable=False, index=True)
    proposed_action = Column(String, nullable=False)
    proposed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    proposed_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(Text, nullable=True)
    last_stage = Column(String, nullable=True)
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)


class ApprovalHistory(Base):
    __tablename__ = "approval_history"
    id = Column(Integer, primary_key=True)
    review_item_id = Column(Integer, ForeignKey("review_item.id"), nullable=False)
    stage = Column(String, nullable=False)
    action = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    review_item_id = Column(Integer, ForeignKey("review_item.id"), nullable=False)
    action = Column(String, nullable=False)
    applied_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)
    details = Column(Text, nullable=True)
