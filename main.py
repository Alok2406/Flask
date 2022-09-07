
from flask import Flask,render_template,request,session,redirect
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json,os,math
from datetime import datetime


with open('confg.json','r') as c:
    params=json.load(c)["params"]

local_server="True"    
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config['UPLOAD_FOLDER']=params['upload_location']


app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['production_uri']

db = SQLAlchemy(app)


class Contact(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False)
    phone= db.Column(db.String(13), nullable=False)
    message= db.Column(db.String(80), nullable=False)
    date= db.Column(db.String(20), nullable=False)



@app.route("/contact",methods=['GET','POST'] )
def contact():
    if (request.method=='POST'):
        #add entry to database
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')
        entry=Contact ( name=name,email=email,phone=phone,date=datetime.now(),message=message)
        db.session.add(entry)
        db.session.commit()
        #to get deatails on admin gmail  
        mail.send_message(  'New message from CodeHash '+ name,
                            sender=email,
                            recipients=[params['gmail-user']],
                            body=message+ "\n" +phone
                            )
    flash("We have recived your message","success")
    return render_template('contact.html',params=params)



@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/login')





@app.route("/login",methods=['GET','POST'])
def signin():
    if('user' in session and session['user']==params['admin_username']):
        posts=Posts.query.all()
        return render_template('adm_pan.html',params=params,posts=posts)

    if request.method=='POST':
        #way to admin panel
        username=request.form.get('username')
        password=request.form.get('password')
        if(username==params['admin_username'] and password==params['admin_password']):
            #set session variable
            session['user']=username
            posts=Posts.query.all()
            return render_template('adm_pan.html',params=params,posts=posts)

    return render_template('signin.html',params=params)


@app.route("/")
def home():
    flash("Welcome to CodeDash")
    flash("hi from codedash","success")
    posts=Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    #[0:params['no_of_posts']]
    
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    
    # To bring older post & Newer post button to work
    #First page
    if(page==1):
        prev="#"
        next="/?page="+ str(page+1)
    elif(page==last):
        prev="/?page="+ str(page-1)
        next="#"
    else:
        prev="/?page="+ str(page-1)
        next="/?page="+ str(page+1)

    #prev page=#(none)
    #next page=Page+1

    #Middle
    #prev page=Page-1
    #next page=Page+1
    #Last
    #prev page=Page+1
    #next page=#(none)

    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)






class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), nullable=False)
    sub_head = db.Column(db.String(30), nullable=False)
    content= db.Column(db.String(800), nullable=False)
    image=db.Column(db.String(80), nullable=False)
    author=db.Column(db.String(80), nullable=False)
    date= db.Column(db.String(40), nullable=False)



@app.route("/post/<string:post_slug>",methods=['GET'])
def post_page(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    
    return render_template('post.html',params=params,post=post)


#to edit the post
@app.route("/editpost/<string:sno>",methods=['GET','POST'])
def editpost(sno):
    if('user' in session and session['user']==params['admin_username']):
        if request.method=='POST':
            post_title = request.form.get('title')
            post_slug =  request.form.get('slug')
            post_shead =  request.form.get('shead')
            post_author =  request.form.get('author')
            post_content=  request.form.get('content')
            post_image=  request.form.get('image')
            date=datetime.now()
            if sno=='0':
                post=Posts (title=post_title,slug=post_slug,sub_head=post_shead,content=post_content,author=post_author,image=post_image,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title =  post_title
                post.slug =  post_slug 
                post.shead =  post_shead
                post.author =  post_author
                post.content=  post_content
                post.image=  post_image
                post.date=date
                db.session.commit()
                return redirect ('/editpost/'+sno)
        post=Posts.query.filter_by(sno=sno).first()
        return render_template('editpost.html',params=params,post=post,sno=sno)


#to upload a file
@app.route("/uploader",methods=['GET','POST'])
def uploader():
    if('user' in session and session['user']==params['admin_username']):
        if request.method=='POST':
            ufile= request.files['fileupload']
            ufile.save (os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(ufile.filename) ))
            flash("upload Succesfull","success")
            return redirect('/login')


#to delete a post
@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if('user' in session and session['user']==params['admin_username']):
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/login')


app.run(debug=True)   
