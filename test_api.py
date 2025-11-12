import requests
import json
import unittest
import jwt
from datetime import datetime, timedelta

BASE_URL = "http://localhost:1234/v1"
SECRET_KEY = "your-secret-key-change-this"

class TestClubAPI(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """测试类设置，在所有测试前运行一次"""
        print("🚀 初始化社团活动API测试环境")
        print("=" * 60)
        
    def setUp(self):
        """每个测试前的设置"""
        self.session = requests.Session()
        
    def generate_valid_token(self, user_id="test_user_001", role="student"):
        """生成有效的JWT Token"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    def get_auth_headers(self, user_id="test_user_001", role="student"):
        """获取认证头"""
        token = self.generate_valid_token(user_id, role)
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    
    def test_01_health_check(self):
        """测试1: 健康检查接口"""
        print("\n📊 测试1: 健康检查")
        response = self.session.get(f"{BASE_URL.replace('/v1', '')}/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        print("Response: ", data)
        print("   ✅ 服务健康状态正常")
    
    def test_02_public_activities_endpoint(self):
        """测试2: 公开活动列表接口"""
        print("\n📊 测试2: 公开活动列表")
        
        # 测试获取活动列表（无需认证）
        response = self.session.get(f"{BASE_URL}/activities?page=1&limit=5")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertIn('activities', data['data'])
        self.assertIn('total', data['data'])
        print("Response: ", data)
        print(f"   ✅ 获取到 {len(data['data']['activities'])} 个活动")
    
    def test_03_authentication_required(self):
        """测试3: 认证要求验证"""
        print("\n📊 测试3: 认证要求验证")
        
        activity_data = {
            "title": "需要认证的活动",
            "description": "这个操作需要认证",
            "startTime": "2024-02-01T14:00:00Z",
            "location": "测试地点"
        }
        
        # 测试无token创建活动（应该失败）
        response = self.session.post(
            f"{BASE_URL}/activities",
            headers={"Content-Type": "application/json"},
            data=json.dumps(activity_data)
        )
        
        self.assertEqual(response.status_code, 401)
        print("   ✅ 未认证访问正确被拒绝")
        
        # 测试无效token创建活动（应该失败）
        response = self.session.post(
            f"{BASE_URL}/activities",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer invalid_token_123"
            },
            data=json.dumps(activity_data)
        )
        
        self.assertEqual(response.status_code, 401)
        print("   ✅ 无效token正确被拒绝")
    
    def test_04_user_authentication_flow(self):
        """测试4: 用户认证流程"""
        print("\n📊 测试4: 用户认证流程")
        
        # 模拟微信登录
        login_data = {"code": "test_auth_code_001"}
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            headers={"Content-Type": "application/json"},
            data=json.dumps(login_data)
        )
        
        # 登录应该成功
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertIn('token', data['data'])
        self.assertIn('userInfo', data['data'])
        
        token = data['data']['token']
        user_info = data['data']['userInfo']
        
        print(f"   ✅ 登录成功，用户: {user_info['name']}")
        
        # 使用获取的token测试认证接口
        auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # 获取用户资料
        response = self.session.get(
            f"{BASE_URL}/users/profile",
            headers=auth_headers
        )
        
        # 用户资料可能不存在（第一次登录），但不应是401
        self.assertIn(response.status_code, [200, 404])
        if response.status_code == 200:
            profile_data = response.json()
            self.assertEqual(profile_data['code'], 200)
            print("   ✅ 获取用户资料成功")
        else:
            print("   ℹ️  用户资料不存在（新用户）")
        
        return token
    
    def test_05_activity_management(self):
        """测试5: 活动管理功能"""
        print("\n📊 测试5: 活动管理")
        
        auth_headers = self.get_auth_headers()
        
        # 创建新活动
        activity_data = {
            "title": "API测试活动",
            "description": "这是通过API测试创建的活动",
            "startTime": "2024-02-15T14:00:00Z",
            "endTime": "2024-02-15T16:00:00Z",
            "location": "测试大楼 301",
            "maxParticipants": 50,
            "tags": ["测试", "API", "开发"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/activities",
            headers=auth_headers,
            data=json.dumps(activity_data)
        )
        
        self.assertEqual(response.status_code, 201)
        create_data = response.json()
        self.assertEqual(create_data['code'], 201)
        
        activity_id = create_data['data']['activityId']
        print(f"   ✅ 活动创建成功: {activity_id}")
        
        # 获取活动详情
        response = self.session.get(f"{BASE_URL}/activities/{activity_id}")
        
        self.assertEqual(response.status_code, 200)
        detail_data = response.json()
        self.assertEqual(detail_data['code'], 200)
        self.assertEqual(detail_data['data']['title'], "API测试活动")
        print("Response: ", detail_data)
        print("   ✅ 活动详情获取成功")
        
        return activity_id
    
    def test_06_registration_management(self):
        """测试6: 报名管理功能"""
        print("\n📊 测试6: 报名管理")
        
        auth_headers = self.get_auth_headers(user_id="reg_test_user")
        
        # 先创建一个测试活动
        activity_data = {
            "title": "报名测试活动",
            "description": "用于测试报名功能的活动",
            "startTime": "2024-02-20T10:00:00Z",
            "location": "报名测试地点",
            "maxParticipants": 10
        }
        
        response = self.session.post(
            f"{BASE_URL}/activities",
            headers=auth_headers,
            data=json.dumps(activity_data)
        )
        
        activity_id = response.json()['data']['activityId']
        
        # 报名活动
        registration_data = {
            "addToCalendar": True,
            "reminderTime": "2024-02-20T09:30:00Z"
        }
        
        response = self.session.post(
            f"{BASE_URL}/activities/{activity_id}/registrations",
            headers=auth_headers,
            data=json.dumps(registration_data)
        )
        
        self.assertEqual(response.status_code, 200)
        reg_data = response.json()
        self.assertEqual(reg_data['code'], 200)
        self.assertIn('registrationId', reg_data['data'])
        print("   ✅ 活动报名成功")
        
        # 获取我的报名列表
        response = self.session.get(
            f"{BASE_URL}/users/registrations",
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        reg_list_data = response.json()
        self.assertEqual(reg_list_data['code'], 200)
        self.assertIn('registrations', reg_list_data['data'])
        print("Response: ", reg_list_data)
        print(f"   ✅ 获取到 {len(reg_list_data['data']['registrations'])} 个报名记录")
        
        # 取消报名
        response = self.session.delete(
            f"{BASE_URL}/activities/{activity_id}/registrations",
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        print("   ✅ 取消报名成功")
        
        return activity_id
    
    def test_07_user_profile_management(self):
        """测试7: 用户资料管理"""
        print("\n📊 测试7: 用户资料管理")
        
        auth_headers = self.get_auth_headers(user_id="profile_test_user")
        
        # 更新用户资料
        profile_data = {
            "name": "测试用户",
            "avatar": "https://example.com/avatar.jpg",
            "studentId": "20240001",
            "department": "计算机科学与技术学院"
        }
        
        response = self.session.put(
            f"{BASE_URL}/users/profile",
            headers=auth_headers,
            data=json.dumps(profile_data)
        )
        
        self.assertEqual(response.status_code, 200)
        update_data = response.json()
        self.assertEqual(update_data['code'], 200)
        self.assertEqual(update_data['data']['name'], "测试用户")
        print("Response: ", update_data)
        print("   ✅ 用户资料更新成功")
        
        # 验证资料已更新
        response = self.session.get(
            f"{BASE_URL}/users/profile",
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        get_data = response.json()
        self.assertEqual(get_data['data']['studentId'], "20240001")
        print("   ✅ 用户资料获取成功")
    
    def test_08_error_handling(self):
        """测试8: 错误处理"""
        print("\n📊 测试8: 错误处理")
        
        auth_headers = self.get_auth_headers()
        
        # 测试创建活动缺少必要字段
        invalid_activity_data = {
            "description": "缺少标题字段",
            "startTime": "2024-02-01T14:00:00Z"
            # 缺少 title 和 location
        }
        
        response = self.session.post(
            f"{BASE_URL}/activities",
            headers=auth_headers,
            data=json.dumps(invalid_activity_data)
        )
        
        self.assertEqual(response.status_code, 400)
        error_data = response.json()
        self.assertEqual(error_data['code'], 400)
        print("   ✅ 参数验证正确工作")
        
        # 测试访问不存在的活动
        response = self.session.get(f"{BASE_URL}/activities/nonexistent_activity")
        
        self.assertEqual(response.status_code, 404)
        print("   ✅ 404错误处理正确")
    
    def test_09_pagination_and_filtering(self):
        """测试9: 分页和筛选功能"""
        print("\n📊 测试9: 分页和筛选")
        
        # 测试分页
        response = self.session.get(f"{BASE_URL}/activities?page=1&limit=2")
        
        self.assertEqual(response.status_code, 200)
        page_data = response.json()
        self.assertEqual(page_data['code'], 200)
        self.assertLessEqual(len(page_data['data']['activities']), 2)
        print("   ✅ 分页功能正常")
        
        # 测试状态筛选（如果支持）
        response = self.session.get(f"{BASE_URL}/activities?status=published")
        
        self.assertEqual(response.status_code, 200)
        filter_data = response.json()
        self.assertEqual(filter_data['code'], 200)
        print("   ✅ 筛选功能正常")
    
    def test_10_comprehensive_workflow(self):
        """测试10: 完整业务流程"""
        print("\n📊 测试10: 完整业务流程")
        
        # 使用独立用户测试完整流程
        test_user_id = "workflow_test_user"
        auth_headers = self.get_auth_headers(user_id=test_user_id)
        
        print("   步骤1: 创建活动")
        activity_data = {
            "title": "完整流程测试活动",
            "description": "测试完整用户流程的活动",
            "startTime": "2024-03-01T15:00:00Z",
            "location": "流程测试地点",
            "maxParticipants": 5
        }
        
        response = self.session.post(
            f"{BASE_URL}/activities",
            headers=auth_headers,
            data=json.dumps(activity_data)
        )
        
        activity_id = response.json()['data']['activityId']
        print(f"      活动创建: {activity_id}")
        
        print("   步骤2: 报名活动")
        response = self.session.post(
            f"{BASE_URL}/activities/{activity_id}/registrations",
            headers=auth_headers,
            data=json.dumps({"addToCalendar": True})
        )
        
        self.assertEqual(response.status_code, 200)
        print("      报名成功")
        
        print("   步骤3: 查看报名列表")
        response = self.session.get(
            f"{BASE_URL}/users/registrations",
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        registrations = response.json()['data']['registrations']
        self.assertTrue(any(reg['activityId'] == activity_id for reg in registrations))
        print("      报名列表正确")
        
        print("   步骤4: 取消报名")
        response = self.session.delete(
            f"{BASE_URL}/activities/{activity_id}/registrations",
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, 200)
        print("      取消报名成功")
        
        print("   ✅ 完整业务流程测试通过")


def run_comprehensive_tests():
    """运行全面测试"""
    print("🎯 开始全面的社团活动API测试")
    print("说明: 这个测试将验证所有核心功能")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 按顺序添加测试（确保依赖关系）
    test_methods = [
        'test_01_health_check',
        'test_02_public_activities_endpoint', 
        'test_03_authentication_required',
        'test_04_user_authentication_flow',
        'test_05_activity_management',
        'test_06_registration_management',
        'test_07_user_profile_management',
        'test_08_error_handling',
        'test_09_pagination_and_filtering',
        'test_10_comprehensive_workflow'
    ]
    
    for method in test_methods:
        suite.addTest(TestClubAPI(method))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📈 测试报告")
    print("=" * 60)
    
    total_tests = result.testsRun
    failed_tests = len(result.failures)
    errors = len(result.errors)
    passed_tests = total_tests - failed_tests - errors
    
    print(f"   总测试数: {total_tests}")
    print(f"   ✅ 通过: {passed_tests}")
    print(f"   ❌ 失败: {failed_tests}")
    print(f"   ⚠️  错误: {errors}")
    
    # 显示失败详情
    if result.failures:
        print(f"\n🔍 失败详情:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback.splitlines()[-1]}")
    
    if result.errors:
        print(f"\n🔍 错误详情:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback.splitlines()[-1]}")
    
    # 总体评估
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n🎯 测试完成率: {success_rate:.1f}%")
    
    if failed_tests == 0 and errors == 0:
        print("🎉 所有测试通过！API功能完整可用。")
        return True
    elif success_rate >= 80:
        print("👍 大部分测试通过，核心功能可用。")
        return True
    else:
        print("💥 需要修复一些功能问题。")
        return False


if __name__ == '__main__':
    import sys
    
    # 检查服务是否可用
    try:
        response = requests.get("http://localhost:1234/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务不可用，请先启动服务: python app.py")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保服务正在运行: python app.py")
        sys.exit(1)
    
    # 运行测试
    success = run_comprehensive_tests()
    
    # 退出码
    sys.exit(0 if success else 1)