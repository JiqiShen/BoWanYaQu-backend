from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required

user_bp = Blueprint('user', __name__)

# 模拟用户数据
users_db = {
    'user_123': {
        'userId': 'user_123',
        'name': '张三',
        'avatar': 'https://avatar.url/zhangsan.png',
        'role': 'student',
        'studentId': '2001210000',
        'department': '计算机学院'
    }
}

@user_bp.route('/users/profile', methods=['GET'])
@token_required
def get_user_profile():
    """获取用户信息"""
    user = users_db.get(g.user_id)
    
    if not user:
        return jsonify({
            "code": 404,
            "message": "用户不存在"
        }), 404
    
    return jsonify({
        "code": 200,
        "data": user
    })

@user_bp.route('/users/profile', methods=['PUT'])
@token_required
def update_user_profile():
    """更新用户信息"""
    data = request.get_json()
    
    if g.user_id not in users_db:
        users_db[g.user_id] = {'userId': g.user_id}
    
    # 更新用户信息
    update_fields = ['name', 'avatar', 'studentId', 'department']
    for field in update_fields:
        if field in data:
            users_db[g.user_id][field] = data[field]
    
    return jsonify({
        "code": 200,
        "message": "更新成功",
        "data": users_db[g.user_id]
    })