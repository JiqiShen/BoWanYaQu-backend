from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required
from models import db, User

user_bp = Blueprint('user', __name__)

@user_bp.route('/user/profile', methods=['GET'])
@token_required
def get_user_profile():
    """获取用户信息"""
    user = User.query.get(int(g.user_id))
    
    if not user:
        return jsonify({
            "code": 404,
            "message": "用户不存在"
        }), 404
    
    return jsonify({
        "code": 200,
        "data": user.to_dict()
    })

@user_bp.route('/user/profile', methods=['PUT'])
@token_required
def update_user_profile():
    """修改用户信息"""
    data = request.get_json()
    
    user = User.query.get(int(g.user_id))
    if not user:
        return jsonify({
            "code": 404,
            "message": "用户不存在"
        }), 404
    
    # 检查用户名是否已存在（如果要更新用户名）
    if 'username' in data and data['username'] != user.username:
        if User.query.filter(User.username == data['username'], User.id != user.id).first():
            return jsonify({
                "code": 400,
                "message": "用户名已存在"
            }), 400
    
    try:
        # 更新用户信息
        update_fields = ['username', 'email', 'phone', 'college', 'major', 'grade', 'avatar']
        for field in update_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "message": "修改成功",
            "data": user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"更新失败: {str(e)}"
        }), 500