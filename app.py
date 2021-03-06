from distutils.log import debug
import os
from flask import *
from flask_sqlalchemy import SQLAlchemy
from secure import secure_filename
from flask_login import UserMixin, LoginManager, login_required, current_user, login_user, logout_user
import qrcode
import qrcode.image.svg
from io import BytesIO
from flask_admin import Admin, expose
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
login_manager = LoginManager(app)
login_manager.login_view = "login"
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///test.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_PATH'] = 5242880
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "HAPPYBIRTHDAYSUCHARA"
db = SQLAlchemy(app)


extens = ['jpg', 'gif', 'mp3', 'png', 'mp4']

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    path = db.Column(db.String, nullable=True)
    role = db.Column(db.String, default='chort')

    def __repr__(self):
        return '<User %r>' % self.username

class MicroBlogModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

# db.drop_all()

db.create_all()
admin = Admin(app)
admin.add_view(MicroBlogModelView(User, db.session))    

@login_manager.user_loader
def load_user(user_id):
    return Get_Load(user_id)


def Get_Load(user_id):
    return User.query.get(user_id)


@app.route('/login', methods = ['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        u = User.query.filter_by(username=login).first()
        if not u:
            u = User(username=login, password=password)
            db.session.add(u)
            db.session.commit()
            login_user(u)
        if u.password == password:
            login_user(u)
        else:
            abort(400, '4ort')
        return redirect(url_for('index'))

    return render_template('pages/login.html')


@app.route('/', methods = ['GET'])
@login_required
def index():
    return render_template('pages/index.html')


@app.route('/uploader', methods = ['POST'])
@login_required
def upload_file():
    f = request.files['file']
    if f.filename != '':
        exten = f.filename.split(".")[-1]
        if exten not in extens:
            return redirect(url_for("index"))
        print(exten)
        try:
            os.remove('static/' + current_user.path)
        except Exception as e:
            print(str(e))
        filename = secure_filename(f.filename)
        filename = str(current_user.id) + "_" + filename
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        current_user.path = os.path.join('uploads/', filename)
        db.session.commit()
    # f.save(secure_filename(f.filename))
    # f.save(os.path.join(app.config['UPLOAD_FOLDER'], f))
    return redirect(url_for('view_page', id=current_user.id))


@app.route('/view/<int:id>', methods = ['GET'])
def view_page(id):
    u = User.query.get_or_404(id)
    stream = BytesIO()
    print(request.host)
    qr = qrcode.make(request.host + '/view/' + str(id),
                     image_factory=qrcode.image.svg.SvgImage)
    qr.save(stream)
    img = stream.getvalue().decode()
    return render_template('pages/view_page.html', u=u, qr=img)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)