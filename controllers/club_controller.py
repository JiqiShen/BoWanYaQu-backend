from flask import Blueprint, request, jsonify, g
from middleware.auth import token_required

# 创建社团模块蓝图
club_bp = Blueprint('club', __name__)

# 模拟社团数据存储（替代真实数据库）
clubs_db = {
    'club_001': {
        'clubId': 'club_001',
        'name': 'ACM 算法协会',
        'description': '算法竞赛与编程学习',
        'logo': 'https://logo.url/acm.png',
        'category': '科技',
        'memberCount': 150,
        'activityCount': 12,
        'creatorId': 'user_123'  # 社团创建者ID（关联用户）
    },
    'club_002': {
        'clubId': 'club_002',
        'name': '摄影爱好者协会',
        'description': '记录美好瞬间，交流摄影技巧',
        'logo': 'https://logo.url/photo.png',
        'category': '文艺',
        'memberCount': 89,
        'activityCount': 8,
        'creatorId': 'user_456'
    }
}

@club_bp.route('/clubs', methods=['GET'])
def get_clubs():
    """获取社团列表（支持分页和分类筛选）"""
    try:
        # 接收前端请求参数，设置默认值
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category')  # 可选筛选条件：分类
        
        # 1. 筛选社团（按分类）
        filtered_clubs = []
        for club in clubs_db.values():
            # 若传入分类参数，只保留分类匹配的社团
            if category and club.get('category') != category:
                continue
            filtered_clubs.append(club)
        
        # 2. 分页处理
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paged_clubs = filtered_clubs[start_idx:end_idx]
        
        # 3. 按统一格式返回响应
        return jsonify({
            "code": 200,
            "data": {
                "clubs": paged_clubs,
                "total": len(filtered_clubs),  # 筛选后的总社团数
                "page": page,
                "limit": limit
            }
        })
        
    except Exception as e:
        # 异常处理：返回500错误和具体原因
        return jsonify({
            "code": 500,
            "message": f"获取社团列表失败: {str(e)}"
        }), 500

@club_bp.route('/clubs', methods=['POST'])
@token_required
def create_club():
    """创建社团（需登录，仅授权用户可操作）"""
    # 获取前端传入的JSON数据
    data = request.get_json()
    
    # 1. 验证必要字段（名称、分类为必填）
    required_fields = ['name', 'category']
    if not all(field in data for field in required_fields):
        return jsonify({
            "code": 400,
            "message": "缺少必要字段（名称和分类为必填）"
        }), 400
    
    # 2. 验证社团名称唯一性（避免重复创建）
    for club in clubs_db.values():
        if club['name'] == data['name']:
            return jsonify({
                "code": 400,
                "message": "该社团名称已存在"
            }), 400
    
    try:
        # 3. 生成唯一社团ID（格式：club_003、club_004...）
        club_id = f"club_{len(clubs_db) + 1:03d}"
        
        # 4. 组装社团数据（可选字段用get获取，设置默认值）
        new_club = {
            'clubId': club_id,
            'name': data['name'],
            'description': data.get('description', ''),  # 描述可选，默认空字符串
            'logo': data.get('logo', 'https://logo.url/default.png'),  # 默认logo
            'category': data['category'],
            'memberCount': 1,  # 新社团默认创建者1人
            'activityCount': 0,  # 新社团默认无活动
            'creatorId': g.user_id  # 关联创建者ID（从认证中间件获取）
        }
        
        # 5. 存入模拟数据库
        clubs_db[club_id] = new_club
        
        # 6. 返回创建成功响应（包含新社团完整信息）
        return jsonify({
            "code": 201,
            "message": "社团创建成功",
            "data": new_club
        }), 201
        
    except Exception as e:
        # 异常处理：返回500错误和具体原因
        return jsonify({
            "code": 500,
            "message": f"创建社团失败: {str(e)}"
        }), 500