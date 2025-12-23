from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required
from datetime import datetime

club_bp = Blueprint('club', __name__)

# 模拟社团数据
clubs_db = {
    1: {
        'club_id': 1,
        'name': 'ACM算法协会',
        'description': '专注于算法竞赛和编程技能的学术社团',
        'type': '学术科技',
        'contact': 'acm_club@example.com',
        'logo': 'https://example.com/acm_logo.png',
        'member_count': 150,
        'activity_count': 12,
        'created_at': '2023-09-01T00:00:00Z',
        'manager_id': 101
    },
    2: {
        'club_id': 2,
        'name': '篮球社',
        'description': '热爱篮球运动的同学们聚集地',
        'type': '体育健身',
        'contact': 'basketball@example.com',
        'logo': 'https://example.com/basketball_logo.png',
        'member_count': 80,
        'activity_count': 8,
        'created_at': '2023-10-15T00:00:00Z',
        'manager_id': 102
    },
    3: {
        'club_id': 3,
        'name': '摄影协会',
        'description': '用镜头记录美好瞬间',
        'type': '文化艺术',
        'contact': 'photo@example.com',
        'logo': 'https://example.com/photo_logo.png',
        'member_count': 60,
        'activity_count': 6,
        'created_at': '2023-11-20T00:00:00Z',
        'manager_id': 103
    }
}

# 关注关系数据
follows_db = {
    # user_id: [club_id1, club_id2, ...]
    1: [1, 2],  # 用户1关注了社团1和2
    2: [3]      # 用户2关注了社团3
}

# 活动数据（从activity_controller导入）
from controllers.activity_controller import activities_db

@club_bp.route('/clubs', methods=['GET'])
def get_clubs():
    """获取社团列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search', '')
        club_type = request.args.get('type', '')
        
        # 筛选社团
        filtered_clubs = []
        for club in clubs_db.values():
            # 搜索筛选
            if search and search.lower() not in club['name'].lower() and search.lower() not in club['description'].lower():
                continue
                
            # 类型筛选
            if club_type and club['type'] != club_type:
                continue
            
            club_data = club.copy()
            
            # 检查是否已关注（如果用户已登录）
            if hasattr(g, 'user_id'):
                try:
                    user_id_int = int(g.user_id)
                    club_data['is_followed'] = user_id_int in follows_db and club['club_id'] in follows_db[user_id_int]
                except (ValueError, TypeError):
                    club_data['is_followed'] = False
            else:
                club_data['is_followed'] = False
            
            filtered_clubs.append(club_data)
        
        # 分页
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paged_clubs = filtered_clubs[start_idx:end_idx]
        
        return jsonify({
            "code": 200,
            "data": {
                "clubs": paged_clubs,
                "total": len(filtered_clubs),
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
    club = clubs_db.get(club_id)
    
    if not club:
        return jsonify({
            "code": 404,
            "message": "社团不存在"
        }), 404
    
    try:
        user_id_int = int(g.user_id)
        
        # 获取最近活动
        recent_activities = []
        for activity in activities_db.values():
            if activity.get('clubInfo', {}).get('clubId') == f"club_{club_id:03d}":
                recent_activities.append({
                    'activity_id': int(activity['activityId'].split('_')[1]),
                    'title': activity['title'],
                    'start_time': activity['startTime'],
                    'end_time': activity.get('endTime', ''),
                    'tag': activity.get('tags', [])[0] if activity.get('tags') else '',
                    'participant_count': activity['currentParticipants'],
                    'max_participants': activity['maxParticipants']
                })
        
        # 只取最近5个活动
        recent_activities = recent_activities[:5]
        
        club_detail = club.copy()
        club_detail.update({
            'is_followed': user_id_int in follows_db and club_id in follows_db[user_id_int],
            'recent_activities': recent_activities
        })
        
        return jsonify({
            "code": 200,
            "data": club_detail
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"用户ID格式错误: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取社团详情失败: {str(e)}"
        }), 500

@club_bp.route('/clubs/<int:club_id>/follow', methods=['POST'])
@token_required
def follow_club(club_id):
    """关注社团"""
    club = clubs_db.get(club_id)
    
    if not club:
        return jsonify({
            "code": 404,
            "message": "社团不存在"
        }), 404
    
    try:
        user_id_int = int(g.user_id)
        
        # 初始化关注列表
        if user_id_int not in follows_db:
            follows_db[user_id_int] = []
        
        # 检查是否已关注
        if club_id in follows_db[user_id_int]:
            return jsonify({
                "code": 400,
                "message": "已关注该社团"
            }), 400
        
        # 关注社团
        follows_db[user_id_int].append(club_id)
        
        # 更新社团关注人数（模拟）
        clubs_db[club_id]['member_count'] += 1
        
        return jsonify({
            "code": 200,
            "message": "关注成功"
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"用户ID格式错误: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"关注失败: {str(e)}"
        }), 500

@club_bp.route('/clubs/<int:club_id>/follow', methods=['DELETE'])
@token_required
def unfollow_club(club_id):
    """取消关注社团"""
    club = clubs_db.get(club_id)
    
    if not club:
        return jsonify({
            "code": 404,
            "message": "社团不存在"
        }), 404
    
    try:
        user_id_int = int(g.user_id)
        
        # 检查是否已关注
        if user_id_int not in follows_db or club_id not in follows_db[user_id_int]:
            return jsonify({
                "code": 400,
                "message": "未关注该社团"
            }), 400
        
        # 取消关注
        follows_db[user_id_int].remove(club_id)
        
        # 更新社团关注人数（模拟）
        if clubs_db[club_id]['member_count'] > 0:
            clubs_db[club_id]['member_count'] -= 1
        
        # 如果用户不再关注任何社团，删除该用户的关注记录
        if not follows_db[user_id_int]:
            del follows_db[user_id_int]
        
        return jsonify({
            "code": 200,
            "message": "取消关注成功"
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"用户ID格式错误: {str(e)}"
        }), 400
    except Exception as e:
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
        
        user_id_int = int(g.user_id)
        
        # 获取关注的社团ID列表
        followed_club_ids = follows_db.get(user_id_int, [])
        
        # 获取社团详情
        followed_clubs = []
        for club_id in followed_club_ids:
            club = clubs_db.get(club_id)
            if club:
                club_data = club.copy()
                club_data['is_followed'] = True
                followed_clubs.append(club_data)
        
        # 分页
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paged_clubs = followed_clubs[start_idx:end_idx]
        
        return jsonify({
            "code": 200,
            "data": {
                "clubs": paged_clubs,
                "total": len(followed_clubs),
                "page": page,
                "limit": limit
            }
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({
            "code": 400,
            "message": f"用户ID格式错误: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取关注社团失败: {str(e)}"
        }), 500