from flask import Blueprint, request, jsonify, g
import requests
from config import Config
from middleware.auth import generate_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """微信登录"""
    data = request.get_json()
    code = data.get('code')
    
    if not code:
        return jsonify({"code": 400, "message": "缺少code参数"}), 400
    
    try:
        # 调用微信接口获取openid (这里需要真实的微信小程序配置)
        wechat_url = f"https://api.weixin.qq.com/sns/jscode2session"
        params = {
            'appid': Config.WECHAT_APP_ID,
            'secret': Config.WECHAT_APP_SECRET,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        # 实际开发中需要调用微信接口，这里模拟返回
        # response = requests.get(wechat_url, params=params)
        # wechat_data = response.json()
        
        # 模拟用户数据
        openid = f"mock_openid_{code}"
        user_info = {
            'userId': f"user_{openid[-8:]}",
            'name': f"用户{openid[-6:]}",
            'avatar': "https://avatar.url/default.png",
            'role': 'student'
        }
        
        # 生成token
        token = generate_token(user_info['userId'], user_info['role'])
        
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": token,
                "userInfo": user_info
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"登录失败: {str(e)}"
        }), 500

@auth_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新Token"""
    # 在实际应用中需要验证refresh token
    # 这里简化处理，重新生成token
    token = generate_token(g.user_id, g.user_role)
    
    return jsonify({
        "code": 200,
        "message": "Token刷新成功",
        "data": {
            "token": token
        }
    })