import os
from datetime import timedelta

class Config:
    # 基础配置
    BASE_API_URL = "http://localhost:1234/v1"
    JSON_AS_ASCII = False
    
    # JWT配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # 数据库配置
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(BASE_DIR, "club_activities.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设置为True可以查看SQL语句
    
    # 错误码
    ERROR_CODES = {
        200: "成功",
        400: "请求参数错误", 
        401: "未授权",
        403: "权限不足",
        404: "资源不存在",
        500: "服务器内部错误"
    }
    
    BUSINESS_ERRORS = {
        1001: "活动不存在",
        1002: "活动已结束", 
        1003: "活动名额已满",
        1004: "您已报名该活动",
        1005: "报名时间已截止",
        1006: "用户名已存在",
        1007: "学号已注册",
        1008: "用户名或密码错误",
        1009: "已关注该社团",
        1010: "未关注该社团",
        1011: "社团不存在",
        1012: "用户不存在",
        1013: "报名记录不存在",
        1014: "权限不足，只有社团管理员可以执行此操作"
    }