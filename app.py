from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Deck, Card
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'bura_cok_gizli_bir_seyler_yaz'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # Kullanıcıyı veritabanından yükler. (current_user olarak)

@app.route('/')
@login_required 
def index():
    return render_template('index.html', user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        new_user = User(
            username=username,
            email=email,
            hash_password=generate_password_hash(password)
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            return f"Bir hata oluştu: {e}"
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
       username = request.form.get("username")
       password = request.form.get("password")
       user = User.query.filter_by(username=username).first()
       if user and check_password_hash(user.hash_password, password):
           login_user(user) #Session'ı otomatik oluşturup tarayıcıya bırakıyor.
           return redirect("/")
       else:
           return render_template('login.html', error="Geçersiz kullanıcı adı veya şifre.")
    return render_template('login.html')



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")


with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run()



