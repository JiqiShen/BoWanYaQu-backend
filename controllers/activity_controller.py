from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required
from datetime import datetime
import time

activity_bp = Blueprint('activity', __name__)

# 模拟数据存储
activities_db = {
    'act_001': {
        'activityId': 'act_001',
        'activity_id': 1,
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
            'club_id': 1,
            'name': 'ACM 算法协会'
        },
        'tags': ['算法', '竞赛', '培训'],
        'registration_end_time': '2024-01-14T23:59:59Z',
        'contact_info': 'acm@example.com',
        'created_at': '2024-01-01T00:00:00Z'
    }
}


# 新增获取最新活动接口
@activity_bp.route('/activities/latest', methods=['GET'])
def get_latest_activities():
    """获取最新活动"""
    try:
        limit = int(request.args.get('limit', 10))
        
        # 获取所有活动并按创建时间排序
        all_activities = list(activities_db.values())
        sorted_activities = sorted(all_activities, 
                                  key=lambda x: x.get('created_at', ''), 
                                  reverse=True)
        
        # 限制数量
        latest_activities = sorted_activities[:limit]
        
        # 格式化返回数据
        formatted_activities = []
        for activity in latest_activities:
            formatted_activities.append({
                'activity_id': activity.get('activity_id', 0),
                'title': activity['title'],
                'club_name': activity['clubInfo']['name'],
                'tag': activity.get('tags', [])[0] if activity.get('tags') else '',
                'participant_count': activity['currentParticipants'],
                'max_participants': activity['maxParticipants']
            })
        
        return jsonify({
            "code": 200,
            "data": {
                "activities": formatted_activities
            }
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取最新活动失败: {str(e)}"
        }), 500

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
            "code": 200,  # 统一使用200
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

@activity_bp.route('/activities/<activity_id>', methods=['GET'])
def get_activity_detail(activity_id):
    """获取活动详情（无需认证也可访问）"""
    # 尝试不同的ID格式
    activity = None
    
    # 如果是数字，尝试构造act_xxx格式
    if activity_id.isdigit():
        activity_key = f"act_{int(activity_id):03d}"
        activity = activities_db.get(activity_key)
    else:
        # 直接查找
        activity = activities_db.get(activity_id)
    
    if not activity:
        return jsonify({
            "code": 404,
            "message": "活动不存在"
        }), 404
    
    # 检查用户是否已报名 (需要认证)
    is_registered = False
    registration_status = 'none'
    
    # 如果有认证头，尝试解析
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        try:
            token = token[7:]
            from middleware.auth import Config
            import jwt
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            user_id = data['user_id']
            
            # 查询报名状态
            from controllers.registration_controller import registrations_db
            registration_key = f"{user_id}_{activity['activity_id']}"
            if registration_key in registrations_db:
                is_registered = True
                registration_status = registrations_db[registration_key].get('status', 'pending')
        except:
            pass
    
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

# 添加获取用户报名成功的活动接口
@activity_bp.route('/user/registered-activities', methods=['GET'])
@token_required
def get_registered_activities():
    """获取报名成功的活动"""
    try:
        user_id_int = int(g.user_id)
        
        # 从registration_controller导入
        from controllers.registration_controller import registrations_db
        
        registered_activities = []
        for reg_key, registration in registrations_db.items():
            if reg_key.startswith(str(user_id_int)) and registration.get('status') == 'approved':
                activity_id = registration['activityId']
                activity = activities_db.get(activity_id)
                
                if activity:
                    registered_activities.append({
                        'activity_id': activity.get('activity_id', 0),
                        'title': activity['title'],
                        'start_time': activity['startTime'],
                        'end_time': activity.get('endTime', ''),
                        'location': activity['location'],
                        'club_name': activity['clubInfo']['name'],
                        'participant_count': activity['currentParticipants'],
                        'max_participants': activity['maxParticipants'],
                        'status': activity['status'],
                        'is_registered': True
                    })
        
        return jsonify({
            "code": 200,
            "data": {
                "activities": registered_activities,
                "total": len(registered_activities)
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
            "message": f"获取报名活动失败: {str(e)}"
        }), 500
    
@activity_bp.route('/activities', methods=['POST'])
@token_required
def create_activity():
    """创建活动"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            "code": 400,
            "message": "请求体必须为JSON格式"
        }), 400
    
    # 验证必要字段
    required_fields = ['title', 'startTime', 'location']
    if not all(field in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": "缺少必要字段：title, startTime, location"
        }), 400
    
    try:
        # 生成活动ID
        activity_id = len(activities_db) + 1
        activity_db_id = f"act_{activity_id:03d}"
        
        # 获取当前用户ID
        user_id = g.user_id if hasattr(g, 'user_id') else 'unknown'
        
        # 创建活动对象
        activity = {
            'activityId': activity_db_id,
            'activity_id': activity_id,
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
                'club_id': data.get('club_id', 1),
                'name': data.get('clubName', '默认社团')
            },
            'tags': data.get('tags', []),
            'registration_end_time': data.get('registration_end_time', ''),
            'contact_info': data.get('contact_info', ''),
            'creatorId': user_id,
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        activities_db[activity_db_id] = activity
        
        return jsonify({
            "code": 200,  # 修改为200，保持统一
            "message": "活动创建成功",
            "data": {
                "activity_id": activity_id,
                "activityId": activity_db_id
            }
        }), 201  # HTTP状态码保持201
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"Fail to create activity: {str(e)}"
        }), 500