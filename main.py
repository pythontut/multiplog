#!/usr/bin/env python
import os
import webapp2
import jinja2

from google.appengine.ext import db

from custom import *

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def render_str(template, **params):
    t = JINJA_ENVIRONMENT.get_template(template)
    return t.render(params)

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created_at = db.DateTimeProperty(auto_now_add=True)

class Handler(webapp2.RequestHandler):
    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_secure_cookie('user_id')
        self.user = user_id and User.find_by_id(int(user_id))

    def write(self, *a, **kw):
        self.response.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        # TODO: Think about implementing make_secure_val as a class method
        cookie_val = Cryptographer().make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and Cryptographer().check_secure_val(cookie_val)

    def login(self, user_id):
        self.set_secure_cookie('user_id', str(user_id))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

class SignUpHandler(Handler):
    def render_signup_form(self, values={}, errors={}):
        self.render('signup.html', values=values, errors=errors)

    def get(self):
        if not self.user:
            self.render_signup_form()
        else:
            self.redirect('/')

    def post(self):
        values = {
          'username': (self.request.get('user') or ''),
          'password': (self.request.get('pswd') or ''),
          'password_confirmation': (self.request.get('pswd_verify') or ''),
          'email': (self.request.get('email') or '')
        }

        new_user = BlogUser(values)
        if new_user.save():
            self.login(new_user.id)
            self.redirect('/')
        else:
            self.render_signup_form(values=values, errors=new_user.errors)

class LogInHandler(Handler):
    def get(self):
        if not self.user:
            self.render('login.html')
        else:
            self.redirect('/')
    def post(self):
        username = self.request.get('user')
        password = self.request.get('pswd')
        if not (username and password):
            self.render('login.html', error='Enter both username and password!')
        else:
            user = User.find_by_username(username)
            if user and Cryptographer().valid_pw(username, password, user.pswd):
                self.login(user.key().id())
                self.redirect('/')
            else:
                self.render('login.html', error='Wrong username and/or  password!')

class LogOutHandler(Handler):
    def get(self):
        self.logout()
        self.redirect('/')

class HomeHandler(Handler):
    def get(self):
        self.render('front.html')

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/signup', SignUpHandler),
    ('/login', LogInHandler),
    ('/logout', LogOutHandler)
], debug=True)
