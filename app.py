import time
from flask.json import jsonify
from werkzeug.security import check_password_hash, generate_password_hash
#
from flask_cors import CORS
# import redis
from redislite import Redis
from flask import Flask, request

app = Flask(__name__)
CORS(app)
# r = redis.Redis(host='localhost', port=6379, db=0, charset='utf-8', decode_responses=True)
r = Redis(r'redislite.db', db=0, charset='utf-8', decode_responses=True)

try:
    keys = r.keys()
    print('Total keys: ', len(keys))
except Exception as e:
    print('ERROR ERROR => ', e)
# except redis.exceptions.AuthenticationError as ae:
#     print('AUTHENTICATION ERROR :: \n', ae)
# except redis.exceptions.ConnectionError as ce:
#     print('CONNECTION ERROR :: \n', ce)

def setup_db():
    'Setting up redis keys to store data.'
    if not r.exists('users'):
        #adding SET `users` key to store distinct user name
        r.sadd('users', 'admin')
    if not r.exists('emails'):
        #adding SET `emails` key to store distinct emails
        r.sadd('emails', 'yourmail@domain.please')
    if not r.exists('phones'):
        #adding SET `phomes` key to store distinct phone numbers
        r.sadd('phones', '0000000000')
    if not r.exists('hits'):
        #adding STRING `hits` key to store total hits on website
        r.set('hits', 0)
    if not r.exists('admin'):
        #adding HAS 'admin` key to store website admins details
        r.hmset(
            'admin', {
                "username": "admin",
                "passwd": "admin",
                "email": "admin-mail@domain.please"
            }
        )
    return 'db created!'
 
def get_hit_count():
    retries = 5
    while True:
        try:
            return r.incr('hits')
        # except redis.exceptions.ConnectionError as exc:
        except Exception as e:
            print('ERROR ERROR => ', e)
            if retries == 0:
                raise e
            retries -= 1
            time.sleep(0.5)
try:
    print(setup_db())
except:
    print('ERROR ERROR ERROR creating database')

@app.route('/', methods=['GET'])
def index():
    count = get_hit_count()
    r.bgsave()
    return 'THIS IS FLASK APP. Hits on website so far is {}'.format(count)

@app.route('/hits', methods=['GET'])
def hello():
    count = get_hit_count()
    return jsonify(
        status=str('OK'),
        msg=str('Total hits on web app is {}'.format(count))
    )

@app.route('/user/set', methods=['POST'])
def setUser():
    if request.method == 'POST':
        form1 = request.form.to_dict()
        # print('Form data:\n', form1)
        uname = form1['uname']
        passwd = generate_password_hash(password=form1['passwd'], method="sha256", salt_length=8)
        email = form1['email']
        phone = form1['phone']
        address = form1['address']
        gender = form1['gender']

        if uname in r.smembers('users'):
            return jsonify(
                status=str('Failed'),
                msg=str('User already exists!')
            )
        if email in r.smembers('emails'):
            return jsonify(
                status=str('Failed'),
                msg=str('Email already exists!')
            )
        if phone in r.smembers('phones'):
            return jsonify(
                status=str('Failed'),
                msg=str('Phone already exists!')
            )
        r.sadd('users', uname)
        r.sadd('emails', email)
        r.sadd('phones', phone)
        r.hmset(
            'user:{}'.format(uname), {
                "uname": uname,
                "passwd": passwd,
                "email": email,
                "phone": phone,
                "address": address,
                "Gender": gender
            }
        )
        return jsonify(
            status=str('OK'),
            msg={
                'msg1':str('Thanks for joining!'),
                'msg2':str('Registered successfully!')
            }
        )

@app.route('/user/get', methods=['POST'])
def getUser():
    if request.method == 'POST':
        form1 = request.form.to_dict()
        uname = form1['uname']
        passwd = form1['passwd']
        if uname not in r.smembers('users'):
            return jsonify(
                status=str('Failed'),
                msg=str("User doesn't exists!")
            )
        pass_hash = r.hget('user:{}'.format(uname), 'passwd')
        resp = dict()
        if check_password_hash(pwhash=pass_hash, password=passwd):
            details = r.hkeys('user:{}'.format(uname))
            for i in details:
                # print(i)
                if i != 'passwd':
                    resp[i] = r.hget('user:{}'.format(uname),i)
            return jsonify(
                status=str('OK'),
                msg=str('Authentication success!'),
                data=resp
            )

        return jsonify(
            status=str('Failed'),
            msg=str('Authentication Failed!')
        )
