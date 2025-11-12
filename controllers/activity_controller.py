from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required

activity_bp = Blueprint('activity', __name__)

# 模拟数据存储
activities_db = {
    'act_001': {
        'activityId': 'act_001',
        'title': '算法竞赛培训',
        'description': '每周算法竞赛培训活动',
        'startTime': '2024-01-15T19:00:00Z',
        'endTime': '2024-01-15T21:00:00Z',
        'location': '理科楼 301',
        'maxParticipants': 100,
        'currentParticipants': 78,
        'status': 'published',
        'clubInfo': {
            'clubId': 'club_001',
            'name': 'ACM 算法协会'
        },
        'tags': ['算法', '竞赛', '培训']
    }
}

@activity_bp.route('/activities', methods=['GET'])
def get_activities():
    """获取活动列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 15))
        status = request.args.get('status', 'published')
        category = request.args.get('category')
        
        # 过滤活动
        filtered_activities = []
        for activity in activities_db.values():
            if status and activity.get('status') != status:
                continue
            if category and activity.get('category') != category:
                continue
            filtered_activities.append(activity)
        
        # 分页
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paged_activities = filtered_activities[start_idx:end_idx]
        
        return jsonify({
            "code": 200,
            "data": {
                "activities": paged_activities,
                "total": len(filtered_activities),
                "page": page,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取活动列表失败: {str(e)}"
        }), 500

@activity_bp.route('/activities', methods=['POST'])
@token_required
def create_activity():
    """创建活动"""
    data = request.get_json()
    
    # 验证必要字段
    required_fields = ['title', 'startTime', 'location']
    if not all(field in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": "缺少必要字段"
        }), 400
    
    try:
        # 生成活动ID
        activity_id = f"act_{len(activities_db) + 1:03d}"
        
        # 创建活动对象
        activity = {
            'activityId': activity_id,
            'title': data['title'],
            'description': data.get('description', ''),
            'startTime': data['startTime'],
            'endTime': data.get('endTime'),
            'location': data['location'],
            'maxParticipants': data.get('maxParticipants', 0),
            'currentParticipants': 0,
            'status': 'published',
            'clubInfo': {
                'clubId': data.get('clubId', 'club_001'),
                'name': data.get('clubName', '默认社团')
            },
            'tags': data.get('tags', []),
            'creatorId': g.user_id
        }
        
        activities_db[activity_id] = activity
        
        return jsonify({
            "code": 201,
            "message": "活动创建成功",
            "data": activity
        }), 201
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Fail to create activity: {str(e)}"
        }), 500

@activity_bp.route('/activities/<activity_id>', methods=['GET'])
def get_activity_detail(activity_id):
    """获取活动详情"""
    activity = activities_db.get(activity_id)
    
    if not activity:
        return jsonify({
            "code": 404,
            "message": "活动不存在"
        }), 404
    
    # 检查用户是否已报名 (需要认证)
    is_registered = False
    registration_status = 'none'
    
    if hasattr(g, 'user_id'):
        # 在实际应用中查询数据库
        is_registered = True  # 模拟数据
        registration_status = 'confirmed'
    
    activity_detail = activity.copy()
    activity_detail.update({
        'isRegistered': is_registered,
        'registrationStatus': registration_status,
        'canRegister': activity['currentParticipants'] < activity['maxParticipants']
    })
    
    return jsonify({
        "code": 200,
        "data": activity_detail
    })