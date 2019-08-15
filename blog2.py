from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators, TextAreaField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import datetime

# Kullanıcı Giriş Decorator'ı ****************************************************************************
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın." , "danger")
            return redirect(url_for("login"))
    return decorated_function
    
# Kullanıcı Kayıt Formu ************************************************************************
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")]) 
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message = "Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula")

# Kullanıcı Login Formu ********************************************************************
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

app = Flask(__name__)
app.secret_key = "bitirme"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/Poyrazz/Desktop/Bitirme_Projesi/Teknik/Python/New/Staj/bitirme_project.db'
db = SQLAlchemy(app)

# SQLite Sunucusuz Veritabanı Kullanıcı Tablosu *******************************************************
class bitirme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    username = db.Column(db.String(80))
    email = db.Column(db.String)
    password = db.Column(db.String)

# SQLite Sunucusuz Veritabanı Makale Tablosu *****************************************************************
class articles3(db.Model):            
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80))
    author = db.Column(db.String(80))
    content = db.Column(db.String)
    created_date = db.Column(db.DateTime, default=datetime.datetime.now) 


numbers = []
for i in range(101):
    numbers.append(i)

@app.route("/")
def index():  
    return render_template("index.html")

@app.route("/ekg")
def ekg():
    return render_template("ekg.html", numbers = numbers)
    
@app.route("/temperature")
def temperature():
    return render_template("temperature.html")

#Kayıt Olma *************************************************************************
@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        # cursor = mysql.connection.cursor()
        # sorgu = "Insert into bitirme(name,email,username,password) VALUES(%s,%s,%s,%s)"
        # cursor.execute(sorgu,(name,email,username,password))
        # mysql.connection.commit()
        # cursor.close()
        varyok = bitirme.query.filter_by(username = username).first()
        if varyok:
            flash("Bu kullanıcı adı daha önce alınmış..." , "danger")
            return redirect(url_for("register"))

        else:
            newbitirme = bitirme(name=name, username=username, email=email, password=password)
            db.session.add(newbitirme)
            db.session.commit()
        
            flash("Başarıyla Kayıt Oldunuz..." , "success")
            return redirect(url_for("login"))
    else:
        if request.method == "POST":
            flash("Başarısız..." , "danger")

        return render_template("register.html", form = form)

# Login İşlemi *************************************************************************
@app.route("/login",methods =["GET","POST"])
def login():
    form = LoginForm(request.form)
    
    if request.method == "POST":
       username = form.username.data
       password_entered = form.password.data

    #    cursor = mysql.connection.cursor()
    #    sorgu = "Select * From bitirme where username = %s"
    #    result = cursor.execute(sorgu,(username,))
       query = bitirme.query.filter_by(username = username).first()

       if query:
           real_password = query.password      # query["password"] >> TypeError: 'bitirme' object is not subscriptable
           if sha256_crypt.verify(password_entered,real_password):
               
               flash("Başarıyla Giriş Yaptınız..." , "success")
               session["logged_in"] = True
               session["username"] = username

               return redirect(url_for("index"))
           else:
               flash("Parolanızı Yanlış Girdiniz..." , "danger")
               return redirect(url_for("login")) 
       else:
           flash("Böyle bir kullanıcı bulunmuyor..." , "danger")
           return redirect(url_for("login"))
    return render_template("login.html",form = form)

# Logout İşlemi ***********************************************************************
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yaptınız..." , "info")
    return redirect(url_for("index"))

# Kontrol Paneli **********************************************************************
@app.route("/dashboard")
@login_required
def dashboard():
    # cursor = mysql.connection.cursor()
    # sorgu = "Select * From articles where author = %s"
    # result = cursor.execute(sorgu,(session["username"],))
    sorgu = articles3.query.filter_by(author = session["username"]).first()
    # Kendi makalesi yoksa hiçbir şey gözükmüyordu ama varsa bütün makaleler gözüküyordu, değiştirildi.
    articles = articles3.query.all()
    if articles:
#        articles = cursor.fetchall()        
        return render_template("dashboard.html",articles = articles, sorgu = sorgu)
    else:
        return render_template("dashboard.html")
    
# Makale Ekleme *******************************************************************
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        # cursor = mysql.connection.cursor()
        # sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        # cursor.execute(sorgu,(title,session["username"],content))
        # mysql.connection.commit()
        # cursor.close()
        newarticles = articles3(title=title, author=session["username"], content=content)
        db.session.add(newarticles)
        db.session.commit()

        flash("Makale Başarıyla Eklendi" , "success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form = form)

# Makale Form ******************************************************************************
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min = 5,max = 100)]) 
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min = 10)])

# Makale Sayfası ********************************************************************
@app.route("/articles")
def articles():
    # cursor = mysql.connection.cursor()
    # sorgu = "Select * From articles"
    # result = cursor.execute(sorgu)
    articles = articles3.query.all()
    if articles:
    #    articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

# Makale İçerik Sayfası *************************************************************
@app.route("/article/<string:id>")
def article(id):
    # cursor = mysql.connection.cursor()  
    # sorgu = "Select * from articles where id = %s"
    # result = cursor.execute(sorgu,(id,))
    article = articles3.query.filter_by(id = id).first()

    if article:
    #    article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

# Makale Silme ***************************************************************************
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    # cursor = mysql.connection.cursor()
    # sorgu = "Select * From articles where author = %s and id = %s"  # 'f' büyük küçük farketmedi.
    # result = cursor.execute(sorgu,(session["username"],id))
    article = articles3.query.filter_by(id = id, author=session["username"]).first()

    if article:
        # article = cursor.fetchone()
        # sorgu2 = "Delete from articles where id = %s"
        # cursor.execute(sorgu2,(id,))
        # mysql.connection.commit()
        db.session.delete(article)
        db.session.commit()

        flash('" {} "  isimli makale silindi'.format(article.title) , "info")    
        # İçiçe tırnak kullanımı.
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok" , "danger")
        return redirect(url_for("index"))

# Makale Güncelleme ****************************************************************
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
   if request.method == "GET":
    #    cursor = mysql.connection.cursor()
    #    sorgu = "Select * from articles where id = %s and author = %s"
    #    result = cursor.execute(sorgu,(id,session["username"]))

       article = articles3.query.filter_by(id = id, author=session["username"]).first()

       if not article:
           flash("Böyle bir makale yok veya bu işleme yetkiniz yok" , "danger")
           return redirect(url_for("index"))
       else:
        #   article = cursor.fetchone()
           form = ArticleForm()

           form.title.data = article.title
           form.content.data = article.content
           return render_template("update.html",form = form)
   else:
       # POST REQUEST ***************************
       form = ArticleForm(request.form)
       article = articles3.query.filter_by(id = id, author=session["username"]).first()

       newTitle = form.title.data
       newContent = form.content.data

    #    sorgu2 = "Update articles Set title = %s,content = %s where id = %s "
    #    cursor = mysql.connection.cursor()
    #    cursor.execute(sorgu2,(newTitle,newContent,id))
    #    mysql.connection.commit()
       article.title = newTitle
       article.content = newContent
       db.session.commit()

       flash("Makale başarıyla güncellendi" , "success")
       return redirect(url_for("dashboard"))

     
# Arama URL *************************************************************************
@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for("index"))     # Siteye gidilmesi istenmiyor, only as post.
   else:
       keyword = request.form.get("keyword")  # articles.html de input ta.

    #    cursor = mysql.connection.cursor()
    #    sorgu = "Select * from articles where title like '%" + keyword +"%'"
    #    result = cursor.execute(sorgu)
       articles = articles3.query.filter(articles3.title == keyword).all() 
    
       if not articles:
           flash("Aranan kelimeye uygun makale bulunamadı..." , "warning")
           return redirect(url_for("articles"))
       else:
           #articles = cursor.fetchall()
           return render_template("articles.html",articles = articles)
    
    
if __name__ == "__main__":
    db.create_all()
    app.run(port=None,debug=True)