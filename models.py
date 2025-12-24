from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    student_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    college = db.Column(db.String(100))
    major = db.Column(db.String(100))
    grade = db.Column(db.String(20))
    avatar = db.Column(db.String(200), default='')
    role = db.Column(db.String(20), default='student')  # student, admin, club_admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    registrations = db.relationship('Registration', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    follows = db.relationship('Follow', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password):
        """验证密码"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'user_id': self.id,
            'username': self.username,
            'student_id': self.student_id,
            'email': self.email or '',
            'phone': self.phone or '',
            'college': self.college or '',
            'major': self.major or '',
            'grade': self.grade or '',
            'avatar': self.avatar or '',
            'role': self.role,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }

class Club(db.Model):
    """社团表"""
    __tablename__ = 'clubs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    type = db.Column(db.String(50), default='学术科技')
    contact = db.Column(db.String(100))
    logo = db.Column(db.String(200))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    activities = db.relationship('Activity', backref='club', lazy='dynamic', cascade='all, delete-orphan')
    follows = db.relationship('Follow', backref='club', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, with_recent_activities=False, user_id=None):
        """转换为字典"""
        data = {
            'club_id': self.id,
            'name': self.name,
            'description': self.description or '',
            'type': self.type,
            'contact': self.contact or '',
            'logo': self.logo or '',
            'manager_id': self.manager_id,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
            'member_count': self.get_member_count(),
            'activity_count': self.activities.count()
        }
        
        if user_id:
            data['is_followed'] = Follow.query.filter_by(user_id=user_id, club_id=self.id).first() is not None
        
        if with_recent_activities:
            # 获取最近5个活动
            recent_activities = self.activities.order_by(Activity.start_time.desc()).limit(5).all()
            data['recent_activities'] = [
                {
                    'activity_id': activity.id,
                    'title': activity.title,
                    'start_time': activity.start_time.isoformat() + 'Z' if activity.start_time else None,
                    'end_time': activity.end_time.isoformat() + 'Z' if activity.end_time else None,
                    'tag': activity.tags.split(',')[0] if activity.tags else '',
                    'participant_count': Registration.query.filter_by(activity_id=activity.id, status='approved').count(),
                    'max_participants': activity.max_participants
                }
                for activity in recent_activities
            ]
        
        return data
    
    def get_member_count(self):
        """获取关注人数"""
        return Follow.query.filter_by(club_id=self.id).count()

class Activity(db.Model):
    """活动表"""
    __tablename__ = 'activities'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime)
    location = db.Column(db.String(200), nullable=False)
    max_participants = db.Column(db.Integer, default=0)
    registration_end_time = db.Column(db.DateTime)
    contact_info = db.Column(db.String(100))
    status = db.Column(db.String(20), default='published')  # published, draft, canceled
    tags = db.Column(db.String(200))  # 用逗号分隔的标签
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    registrations = db.relationship('Registration', backref='activity', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, with_club_info=True, user_id=None):
        """转换为字典"""
        data = {
            'activity_id': self.id,
            'activityId': f"act_{self.id:03d}",
            'title': self.title,
            'description': self.description or '',
            'startTime': self.start_time.isoformat() + 'Z' if self.start_time else None,
            'endTime': self.end_time.isoformat() + 'Z' if self.end_time else None,
            'location': self.location,
            'maxParticipants': self.max_participants,
            'currentParticipants': Registration.query.filter_by(activity_id=self.id, status='approved').count(),
            'status': self.status,
            'registration_end_time': self.registration_end_time.isoformat() + 'Z' if self.registration_end_time else None,
            'contact_info': self.contact_info or '',
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }
        
        if with_club_info and self.club:
            data['clubInfo'] = {
                'clubId': f"club_{self.club.id:03d}",
                'club_id': self.club.id,
                'name': self.club.name
            }
        
        if user_id:
            # 检查用户是否已报名
            registration = Registration.query.filter_by(user_id=user_id, activity_id=self.id).first()
            data['isRegistered'] = registration is not None
            data['registrationStatus'] = registration.status if registration else 'none'
            data['canRegister'] = (Registration.query.filter_by(activity_id=self.id, status='approved').count() < self.max_participants) if self.max_participants > 0 else True
        
        return data

class Registration(db.Model):
    """报名表"""
    __tablename__ = 'registrations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activities.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    add_to_calendar = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.DateTime)
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：一个用户只能报名一次同一个活动
    __table_args__ = (db.UniqueConstraint('user_id', 'activity_id', name='unique_user_activity'),)
    
    def to_dict(self, with_activity_info=False):
        """转换为字典"""
        data = {
            'registrationId': f"reg_{self.id:03d}",
            'user_id': self.user_id,
            'activity_id': self.activity_id,
            'status': self.status,
            'addToCalendar': self.add_to_calendar,
            'reminderTime': self.reminder_time.isoformat() + 'Z' if self.reminder_time else None,
            'registration_time': self.registration_time.isoformat() + 'Z' if self.registration_time else None
        }
        
        if with_activity_info and self.activity:
            data['activityInfo'] = {
                'title': self.activity.title,
                'startTime': self.activity.start_time.isoformat() + 'Z' if self.activity.start_time else None,
                'location': self.activity.location
            }
        
        return data

class Follow(db.Model):
    """关注表"""
    __tablename__ = 'follows'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 唯一约束：一个用户只能关注同一个社团一次
    __table_args__ = (db.UniqueConstraint('user_id', 'club_id', name='unique_user_club'),)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'follow_id': self.id,
            'user_id': self.user_id,
            'club_id': self.club_id,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None
        }