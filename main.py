import calendar
from functools import wraps
from ast import literal_eval
from flask import Flask, request, jsonify, make_response, render_template,redirect
import jwt
import uuid
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chachahcablingblingbling'

def selection(s):
    for i in range(0,len(s)):
        s[i]=s[i].split('|')
    for i in range(0,len(s)-1):
        p=0
        mini=int(s[-1][1])
        for j in range(i,len(s)):
            if int(s[j][1])<=mini:
                mini=int(s[j][1])
                print(mini)
                p=j
        s[i],s[p]=s[p],s[i]
    for i in range(0,len(s)):
        s[i]='|'.join(s[i])
    print(s)
class User:
    def __init__(self, user_id, email, password, first_name, last_name):
        self.user_id = user_id
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name

    def add_user(self):
        record = [self.user_id, self.email, self.password, self.first_name, self.last_name]
        record = '|'.join(record) + '\n'
        with open('root/users.txt', 'a') as f:
            f.write(record)


def token_required(fn):
    @wraps(fn)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        f = open('root/users.txt', 'r')
        current_user = None
        for line in f:
            l = line.split('|')
            if l[0] == data['user_id']:
                current_user = User(l[0], l[1], l[2], l[3], l[4])
                break
        f.close()
        if current_user != None:
            return fn(current_user, *args, **kwargs)
        else:
            return jsonify({'message': 'Token is invalid!', 'x-access-token': token}), 401

    return decorated


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='GET':
        response=make_response(render_template('signin.html'))
        return response
    auth = request.form

    if not auth or not auth.get('email') or not auth.get('password'):
        response = make_response(jsonify({'status': 'Enter valid credentials'}),
                                 401)  # , {'WWW-Authenticate': 'Basic realm="Login required!"'})
    else:
        f = open('root/users.txt', 'r')
        user = None
        for line in f:
            l = line.split('|')
            if l[1] == auth.get('email'):
                user = User(l[0], l[1], l[2], l[3], l[4])
                break
        f.close()

        if not user:
            response = make_response(jsonify({'status': 'Could not find an account associated with the given email'}),
                                     401, )  # {'WWW-Authenticate': 'Basic realm="Login required!"'})

        elif check_password_hash(user.password, auth.get('password')):
            token = jwt.encode(
                {'user_id': user.user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
                app.config['SECRET_KEY'])
            user_data = {}
            user_data['user_id'] = user.user_id
            user_data['first_name'] = user.first_name
            user_data['email'] = user.email

            response = make_response(redirect('/get'))

            response.set_cookie(key='jwt', value=token, httponly=True,  domain='127.0.0.1',
                                secure=False)
        else:
            response = make_response(jsonify({'status': 'Enter valid credentials'}),
                                     401)
            # response.set_cookie('jwt',request.cookies.get('jwt'))# {'WWW-Authenticate': 'Basic realm="Login required!"'})

    return response

@app.route('/signout')
def sign_out():
    response=make_response(redirect('/login'))
    response.set_cookie(key='jwt',value="",httponly=True,  domain='127.0.0.1',
                                                                 secure=False)
    return response

@app.route('/signup', methods=['GET','POST'])
def create_user():
    if request.method=='GET':
        response=make_response(render_template('signup.html'))
        return response
    data = request.form
    f = open('root/users.txt', 'r')
    check_email_existence = None
    for line in f:
        l = line.split('|')
        if l[0] == data.get('email'):
            check_email_existence = True
            break
    f.close()
    if check_email_existence == True:
        return make_response(jsonify({'message': 'Account already exists'}), 500)
    hashed_password = generate_password_hash(data['password'], method='sha256')
    if data.get('first_name') == None or data.get('last_name') == None or data.get('email') == None:
        return make_response(jsonify({'message': 'Invalid data'}), 500)
    new_user = User(str(uuid.uuid4()), data.get('email'), hashed_password, data.get('first_name'),
                    data.get('last_name'))
    new_user.add_user()
    token = jwt.encode(
        {'user_id': new_user.user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
        app.config['SECRET_KEY'])
    user_data = {'user_id': new_user.user_id, 'first_name': new_user.first_name, 'last_name': new_user.last_name,
                 'email': new_user.email}
    response = make_response(make_response(redirect('/get')))
    response.set_cookie(key='jwt', value=token, httponly=True, domain='127.0.0.1', secure=False)
    return response

@app.route('/expandArticle/<month>/<day>/<data>')
@token_required
def expand_article(current_user,month,day,data):
    response=make_response(render_template('article.html',day=day,month=month,data=data))
    response.charset="utf-8"
    return response

@app.route('/get', methods=['GET'])
@token_required
def get(current_user):
    if request.args.get('month')==None:
        month=calendar.month_name[datetime.date.today().month].lower()
    else:
        month=request.args.get('month')
    data = []
    with open('root/months/' + month + '.txt') as f:
        for line in f:
            l = line.split('|')
            if l[0] == current_user.user_id:
                m=calendar.month_name[int(l[2])].title()
                data.append({'month': m, 'day': l[1], 'data': eval(l[3])})


    response = make_response(render_template('temp.html', data=data,month=month,
                                             userdata={'name': current_user.first_name + ' ' + current_user.last_name,
                                                       'email':current_user.email,}))
    response.charset = 'utf-8'
    return response

@app.route('/new',methods=['GET','POST'])
@token_required
def new(current_user):
    if request.method=='GET':
        response=make_response(render_template('write_article.html'))
        return response
    data = request.form
    article = data.get('article_data')
    date=data.get('calender')
    if date=="":
        response=make_response(render_template("write_article.html",invalid_date=True))
        return response
    date=date.split('-')
    # calendar.month_name[datetime.date.today().month].lower()
    today_month_in_letters = calendar.month_name[int(date[1])].lower()
    today_month = int(date[1])
    today_day = int(date[2])
    # calendar.month_name[datetime.date.today().month].lower()
    f = open('root/record_locations.txt', 'r')
    record_offset = None
    for line in f:
        l = line.split('|')
        if l[0] == current_user.user_id:
            f.close()
            break
    else:
        f.close()
        with open('root/months/' + today_month_in_letters + '.txt', 'r') as f:
            bytes_length = len(f.read())
        with open('root/record_locations.txt', 'a') as f:
            record = [current_user.user_id]
            for i in range(1, 13):
                if i == today_month:
                    record.append(str(bytes_length + 1))
                else:
                    record.append('N/A')
            record = '|'.join(record) + '\n'
            f.write(record)
        with open('root/months/' + today_month_in_letters + '.txt', 'a') as diary_of_a_month:
            record = [current_user.user_id, str(today_day), str(today_month), repr(article)]
            record = '|'.join(record) + '\n'
            diary_of_a_month.write(record)
        response=make_response(redirect('/get'))
        return response

    diary_of_a_month = open('root/months/' + today_month_in_letters + '.txt', 'r')
    lines = diary_of_a_month.readlines()
    record = [current_user.user_id, str(today_day), str(today_month), repr(article)]
    record = '|'.join(record) + '\n'
    record_length = len(record)
    for diary_record in lines:
        if diary_record == '\n':
            continue
        rec = diary_record.split('|')
        if rec[1] == str(today_day) and rec[2] == str(today_month) and rec[0] == current_user.user_id:
            response=make_response(render_template('write_article.html',invalid_date=True))
            return response
    diary_of_a_month.close()
    content = ''.join(lines)
    with open('root/months/' + today_month_in_letters + '.txt', 'w') as diary_of_a_month:
        if l[today_month] == 'N/A':
            diary_of_a_month.write(content + record)
            record_offset = len(content) + 1
            l[today_month] = str(record_offset + 1)

        else:
            diary_of_a_month.write(content[:int(l[today_month]) - 1] + record + content[int(l[today_month]) - 1:])
            record_offset = len(content[:int(l[today_month])])
            l[today_month] = str(record_offset + record_length)
    with open('root/record_locations.txt', 'r') as f:
        user_content = f.readlines()
    with open('root/record_locations.txt', 'w') as f:
        record_as_list = record.split('|')
        for i in range(len(user_content)):
            if user_content[i] == '\n':
                continue
            user_data = user_content[i].split('|')
            if user_data[today_month] == 'N/A':
                if user_data[0] == current_user.user_id:
                    user_data[today_month] = str(record_offset)
                else:
                    continue
            elif user_data[0] == current_user.user_id and record_offset == len(content) + 1:
                user_data[today_month] = str(record_offset)
            elif int(user_data[today_month]) > record_offset and user_data[0] != current_user.user_id:
                user_data[today_month] = str(int(user_data[today_month]) + record_length)

            user_content[i] = '|'.join(user_data)
        f.write(''.join(user_content))

    response=make_response(redirect('/get'))
    return response


if __name__ == '__main__':
    app.run(debug=True)
