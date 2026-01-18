from flask import Flask, abort, render_template, request, redirect, url_for
from models import db, User, Deck, Card
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta

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
        # VERİ DOĞRULAMA (Validation)
        # Strip() fonksiyonu ile sadece boşluk tuşuna basıp göndermesini de engelleriz.
        if not username or not password or not email:
            return render_template('register.html', error="Lütfen tüm alanları doldurun!")
    
        if len(username.strip()) < 3:
            return render_template('register.html', error="Kullanıcı adı en az 3 karakter olmalı!")
        if len(password.strip()) < 6:
            return render_template('register.html', error="Şifre en az 6 karakter olmalı!")
        # 1. ÖNCE KONTROL (Kullanıcıya nazikçe bilgi vermek için)
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Bu kullanıcı adı zaten alınmış.")

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error="Bu e-posta zaten kullanımda.")
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

@app.route('/create-deck', methods=['GET', 'POST'])
@login_required
def create_deck():
    if request.method == 'POST':
        name = request.form.get("name")
        if not name or len(name.strip()) < 3:
            return render_template('create_deck.html', error="Deste adı en az 3 karakter olmalı!")
        new_deck = Deck(name=name, user_id=current_user.id)
        try:
            db.session.add(new_deck)
            db.session.commit()
            return redirect(url_for("index"))
        except Exception as e:
            db.session.rollback()
            return f"Bir hata oluştu: {e}"
    return render_template('create_deck.html')

@app.route('/deck/<int:deck_id>')
@login_required
def deck_detail(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if deck.user_id != current_user.id:
        abort(403, description="Bu desteye erişim izniniz yok.")
    return render_template('deck_detail.html', deck=deck)

@app.route('/deck/<int:deck_id>/add-card', methods=['GET', 'POST'])
@login_required
def add_card(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if deck.user_id != current_user.id:
        abort(403, description="Bu desteye erişim izniniz yok.")

    if request.method == 'POST':
        front = request.form.get("front")
        back = request.form.get("back")
        if not front or not back:
            return render_template('deck_detail.html', deck=deck, error="Lütfen her iki tarafı da doldurun!")
        new_card = Card(front=front, back=back, deck_id=deck.id)
        try:
            db.session.add(new_card)
            db.session.commit()
            return redirect(url_for("deck_detail", deck_id=deck.id))
        except Exception as e:
            db.session.rollback()
            return f"Bir hata oluştu: {e}"
    return render_template('add_card.html', deck=deck)

@app.route('/deck/<int:deck_id>/study')
@login_required
def study(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if deck.user_id != current_user.id:
        abort(403, description="Bu desteye erişim izniniz yok.")
    card = Card.query.filter(Card.deck_id == deck.id, Card.next_review <= datetime.now()).first()
    if not card:
        return render_template('study.html', deck=deck, isFinished=True)
    
    return render_template('study.html', card=card, deck=deck, isFinished=False)

@app.route('/deck/<int:deck_id>/review/<int:card_id>/<string:action>')
@login_required
def review_card(deck_id, card_id, action):
    deck = Deck.query.get_or_404(deck_id)
    card = Card.query.get_or_404(card_id)
    if deck.user_id != current_user.id:
        abort(403, description="Bu desteye erişim izniniz yok.")

    if action == 'success': # Bildiyse kutuyu arttır (Seviye atla)
        card.box += 1
        # Kutuna göre mola süresi
        if card.box == 2:
            delay = 3   # 3 gün sonra
        elif card.box == 3:
            delay = 7   # 1 hafta sonra
        elif card.box == 4:
            delay = 14  # 2 hafta sonra
        elif card.box >= 5:
            delay = 30  # 1 ay sonra
        else:
            delay = 1
        # Tarihi ileri at
        card.next_review = datetime.now() + timedelta(days=delay)
        
    elif action == 'fail': # Bilemediyse en başa, 1. kutuya döner.
        card.box = 1
        card.next_review = datetime.now()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Update hatası: {e}") 
        return "Veritabanı güncellenirken bir hata oluştu.", 500

    # Bir sonraki karta geçmek için study sayfasına geri dön
    return redirect(url_for('study', deck_id=deck_id))

with app.app_context():
    db.create_all()
if __name__ == '__main__':
    app.run()