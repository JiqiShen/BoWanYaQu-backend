from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required
from models import db, Club, Follow, Activity, Registration
from sqlalchemy import or_

club_bp = Blueprint('club', __name__)

@club_bp.route('/clubs', methods=['GET'])
def get_clubs():
    """获取社团列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search', '')
        club_type = request.args.get('type', '')
        
        # 构建查询
        query = Club.query
        
        # 搜索筛选
        if search:
            query = query.filter(or_(
                Club.name.ilike(f'%{search}%'),
                Club.description.ilike(f'%{search}%')
            ))
        
        # 类型筛选
        if club_type:
            query = query.filter(Club.type == club_type)
        
        # 获取总数
        total = query.count()
        
        # 分页
        clubs = query.order_by(Club.created_at.desc())\
                    .offset((page - 1) * limit)\
                    .limit(limit)\
                    .all()
        
        # 转换为字典
        user_id = int(g.user_id) if hasattr(g, 'user_id') else None
        clubs_data = [club.to_dict(user_id=user_id) for club in clubs]
        
        return jsonify({
            "code": 200,
            "data": {
                "clubs": clubs_data,
                "total": total,
                "page": page,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取社团列表失败: {str(e)}"
        }), 500

@club_bp.route('/clubs/<int:club_id>', methods=['GET'])
@token_required
def get_club_detail(club_id):
    """获取社团详情"""
    club = Club.query.get(club_id)
    
    if not club:
        return jsonify({
            "code": 404,
            "message": "社团不存在"
        }), 404
    
    try:
        user_id = int(g.user_id)
        club_detail = club.to_dict(with_recent_activities=True, user_id=user_id)
        
        return jsonify({
            "code": 200,
            "data": club_detail
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取社团详情失败: {str(e)}"
        }), 500

@club_bp.route('/clubs/<int:club_id>/follow', methods=['POST'])
@token_required
def follow_club(club_id):
    """关注社团"""
    club = Club.query.get(club_id)
    
    if not club:
        return jsonify({
            "code": 404,
            "message": "社团不存在"
        }), 404
    
    try:
        user_id = int(g.user_id)
        
        # 检查是否已关注
        existing_follow = Follow.query.filter_by(user_id=user_id, club_id=club_id).first()
        if existing_follow:
            return jsonify({
                "code": 400,
                "message": "已关注该社团"
            }), 400
        
        # 创建关注记录
        follow = Follow(user_id=user_id, club_id=club_id)
        db.session.add(follow)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "message": "关注成功"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"关注失败: {str(e)}"
        }), 500

@club_bp.route('/clubs/<int:club_id>/follow', methods=['DELETE'])
@token_required
def unfollow_club(club_id):
    """取消关注社团"""
    club = Club.query.get(club_id)
    
    if not club:
        return jsonify({
            "code": 404,
            "message": "社团不存在"
        }), 404
    
    try:
        user_id = int(g.user_id)
        
        # 检查是否已关注
        follow = Follow.query.filter_by(user_id=user_id, club_id=club_id).first()
        if not follow:
            return jsonify({
                "code": 400,
                "message": "未关注该社团"
            }), 400
        
        # 删除关注记录
        db.session.delete(follow)
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "message": "取消关注成功"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "code": 500,
            "message": f"取消关注失败: {str(e)}"
        }), 500

@club_bp.route('/user/followed-clubs', methods=['GET'])
@token_required
def get_followed_clubs():
    """获取关注的社团"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        user_id = int(g.user_id)
        
        # 查询用户关注的社团
        follows = Follow.query.filter_by(user_id=user_id)
        
        # 获取总数
        total = follows.count()
        
        # 分页
        follows = follows.order_by(Follow.created_at.desc())\
                        .offset((page - 1) * limit)\
                        .limit(limit)\
                        .all()
        
        # 获取社团详情
        clubs_data = []
        for follow in follows:
            club = Club.query.get(follow.club_id)
            if club:
                club_dict = club.to_dict()
                club_dict['is_followed'] = True
                clubs_data.append(club_dict)
        
        return jsonify({
            "code": 200,
            "data": {
                "clubs": clubs_data,
                "total": total,
                "page": page,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取关注社团失败: {str(e)}"
        }), 500