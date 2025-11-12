import os
from datetime import timedelta

class Config:
    # 基础配置
    BASE_API_URL = "http://localhost:1234/v1"
    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', 'wx1234567890abcdef')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', 'your_app_secret')
    JSON_AS_ASCII = False
    
    # JWT配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # 数据库配置 (使用SQLite示例)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///club_activities.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
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
        1005: "报名时间已截止"
    }