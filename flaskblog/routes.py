import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import (RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm, PicPostForm, SearchForm)
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from werkzeug.utils import secure_filename

@app.route("/", methods=['GET', 'POST'])
def first():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/home", methods=['GET', 'POST'])
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/latestposts", methods=['GET', 'POST'])
@login_required
def latest():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).limit(5).paginate(page=page, per_page=5)
    return render_template('latest.html', posts=posts)

@app.route("/about", methods=['GET', 'POST'])
def about():
    return render_template('about.html')

@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    form = SearchForm()
    if form.validate_on_submit():
        # posts = Post.query.filter() order_by(Post.date_posted.desc())
        page = request.args.get('page', 1, type=int)
        if(form.univ.data and form.city.data):
            post = Post.query.filter_by(city =form.city.data).order_by(Post.costpp).paginate(page=page, per_page=5)
        elif(form.univ.data):
            post = Post.query.filter_by(univ=form.univ.data).order_by(Post.date_posted.desc(), Post.costpp.desc()).paginate(page=page, per_page=5)
        else:
            post = Post.query.filter_by(city=form.city.data).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
        flash('Here are your stories!!', 'success')
        return render_template('search_results.html',posts=post)
    return render_template('search.html', title='Search Stories', form=form, legend='Search Stories')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('first'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

def save_pictures(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    file_filename = random_hex + f_ext
    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(os.path.join(app.root_path, 'static/post_pictures', file_filename))
    return (file_filename)

# def save_pictures(form_picture):
#     filenames = []
#     for f in form_picture:
#         filename = secure_filename(f.filename)
#         i = Image.open(f)
#         f.save(os.path.join(
#                     app.root_path, 'static/post_pictures', filename
#                 ))
#         i.save(os.path.join(app.root_path, 'static/post_pictures', filename))
#         print('SAVED!!!!!!!!!!!!!')
#         filenames.append(filename)
#     return filenames
    

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PicPostForm()
    if form.validate_on_submit():
        filenames = []
        #print(type(form.pictures.data))
        #pic = save_pictures(form.pictures.data)
        for f in request.files.getlist('Pictures'):
        #len(uploaded_file)
            print(f.filename)
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(f.filename)
            picture_fn = random_hex + f_ext
            filenames.append(str(picture_fn))
            i = Image.open(f)
            print((i.size))
            # i.resize = 600,400
            i.thumbnail((480,600))
            print((i.size))
            #i.size[0] = 400
            #i.size[1] = 600
            # i.height = 600
            # i.width = 400
            print(type(i))
            #i.thumbnail(600,400)
            # print("Width:"+str(w))
            i.save(os.path.join(app.root_path,'static\\post_pics', secure_filename(picture_fn)))
        post = Post(title=form.title.data, story=form.story.data, author=current_user, images = str(filenames), univ = form.univ.data, city = form.city.data,costpp = form.costpp.data)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PicPostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.univ = form.univ.data
        post.city = form.city.data
        post.costpp = form.costpp.data
        post.story = form.story.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.univ.data = post.univ
        form.city.data = post.city
        form.costpp.data = post.costpp
        form.story.data = post.story
    return render_template('create_post.html', title='Update Post', form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)

@app.route("/posts/<string:univ>")
def univ_posts(univ):
    page = request.args.get('page', 1, type=int)
    #user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(univ=univ)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('univ_posts.html', posts=posts, univ = univ)

@app.route("/posts/<string:city>")
def city_posts(city):
    page = request.args.get('page', 1, type=int)
    #user = User.query.filter_by(username=username).first_or_404()
    #posts = Post.query.filter_by(city=city).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    posts = Post.query.filter_by(city=city).paginate(page=page, per_page=5)
    #print(len(posts))
    return render_template('city_posts.html', posts=posts, city = city)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.errorhandler(404)
def error_404(error):
    return render_template('404_error.html'), 404

