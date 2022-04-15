# -*- coding: utf-8 -*-
import unittest

from watchlist import app, db
from watchlist.models import Movie, User
from watchlist.commands import forge, initdb

class WatchlistTestCase(unittest.TestCase):
    
    def setUp(self):
        # 更新配置
        app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
        
        # 创建数据库和表
        db.create_all()
        
        # 创建测试数据，一个用户，一个电影条目
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie Title', year='2022')
        
        # 使用 all_all() 方法一次添加多个模型类实例，传入列表
        db.session.add_all([user, movie])
        db.session.commit()
        
        # 创建测试客户端和测试命令运行器
        self.client = app.test_client()
        self.runner = app.test_cli_runner()
        
    def tearDown(self):
        # 清除数据库会话，删除数据库表
        db.session.remove()
        db.drop_all()
        
    # 测试程序实例是否存在
    def test_app_exist(self):
        self.assertIsNotNone(app)
        
    # 测试程序是否处于测试模式
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])
        
    # 测试404页面
    def test_404_page(self):
        
        # 调用test_client()类方法, 返回包含响应数据的响应对象
        response = self.client.get('/nothing')
        # 对这个响应对象调用 get_data() 方法并把 as_text 参数设为 True 可以获取 Unicode 格式的响应主体
        data = response.get_data(as_text=True)
        
        # 判断 'Page Not Fount - 404' 在不在响应数据里
        self.assertIn('Page Not Found - 404', data)
        # 判断 'Go Back' 在不在响应数据里
        self.assertIn('Go Back', data)
        # 判断响应状态码是不是 404
        self.assertEqual(response.status_code, 404)
       
        
    # 测试主页
    def test_index_page(self):
        
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        
        self.assertIn('Test\'s Watchlist', data)
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)
        
    
    # 辅助方法，用于登入用户
    def login(self):
        self.client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)
        

    
    # 测试创建条目
    def test_create_item(self):
        self.login()
        
        # 测试创建条目操作
        response = self.client.post('/', data=dict(title='New Movie', year='2022'),follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)
       
       # 测试创建条目操作，但电影标题为空
        response = self.client.post('/', data=dict(title='', year='2022'),follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)
       
       # 测试创建条目操作，但电影年份为空
        response = self.client.post('/', data=dict(title='New Movie', year=''),follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)
    
    
    # 测试更新条目
    def test_update_item(self):
        self.login()
        
        # 测试更新页面
        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit Item', data)
        self.assertIn('Test Movie Title', data)
        self.assertIn('2022', data)
        
        # 测试更新条目操作，但电影标题为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='',
            year='2022'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertIn('Invalid input.', data)

        # 测试更新条目操作，但电影年份为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited Again',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertNotIn('New Movie Edited Again', data)
        self.assertIn('Invalid input.', data)
        
        
    # 测试删除条目
    def test_delete_item(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item Deleted.', data)
        self.assertNotIn('Test Movie Title', data)
        
        
    # 测试登录保护
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
       
        
    # 测试登录
    def test_login(self):
        response = self.client.post('/login', data=dict(username='test', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('<form method="post">', data)
        
        # 测试使用错误的密码登录
        response = self.client.post('/login', data=dict(username='test', password='456'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 测试使用空用户名登录
        response = self.client.post('/login', data=dict(username='', password='123'), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

        # 测试使用空密码登录
        response = self.client.post('/login', data=dict(username='test', password=''), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)
        
    # 测试登出
    def test_logout(self):
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="post">', data)
        
    
    # 测试设置
    def test_settings(self):
        self.login()

        # 测试设置页面
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Settings', data)
        self.assertIn('Your Name', data)

        # 测试更新设置
        response = self.client.post('/settings', data=dict(name='Frank Chen',), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Settings updated.', data)
        self.assertIn('Frank Chen', data)

        # 测试更新设置，名称为空
        response = self.client.post('/settings', data=dict(name='',), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Settings updated.', data)
        self.assertIn('Invalid input.', data)
        
    
    # 测试虚拟数据
    def test_forge_command(self):
        result = self.runner.invoke(forge)
        self.assertIn('Done.', result.output)
        self.assertNotEqual(Movie.query.count(), 0)
        
    # 测试初始化数据库
    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)
        
    # 测试生成管理员账户
    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'james', '--password', '102'])
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'james')
        self.assertTrue(User.query.first().validate_password('102'))
        
    # 测试更新管理员账户
    def test_admin_command_update(self):
        # 使用 args 参数给出完整的命令参数列表
        result = self.runner.invoke(args=['admin', '--username', 'frank', '--password', '1002'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'frank')
        self.assertTrue(User.query.first().validate_password('1002'))
        
    
if __name__ == '__main__':
    unittest.main()