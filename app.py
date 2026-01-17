from flask import Flask
from flask import Flask, render_template, request, redirect
from models import db, User, Deck, Card

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db.init_app(app)


@app.route('/')
def check():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        new_user = User(
            username=username,
            email=email,
            hash_password=password
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            return "Başarılı! Kullanıcı veritabanına eklendi."
        except Exception as e:
            db.session.rollback()
            return f"Bir hata oluştu: {e}"
        
    return render_template('register.html')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()



