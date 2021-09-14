from arp_flask import app, db, bcrypt, mail
from flask import render_template, url_for, redirect, flash, request, jsonify
from arp_flask.forms import RegistrationForm, LoginForm, ResetPasswordForm, ChangePasswordForm, AccountUpdateForm
from arp_flask.models import User, UserDetails, Post, Comment, Like
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message
import os

@app.route('/')
@app.route('/home')
def homepage():
    return render_template('index.html')


######  ADDED STARTED HERE  ######

@app.route('/posts_all', methods=['POST', 'GET'])
@login_required
def posts_all():
    posts = Post.query.all()
    return render_template("posts.html", user=current_user, posts=posts)

######  ADDED ENDED HERE  ######

@app.route('/about')
def about():
    return render_template('about.html', title='About Page')

def save_image(picture_file):
    picture=picture_file.filename
    picture_path=os.path.join(app.root_path,'static/profile_pics', picture)
    picture_file.save(picture_path)
    return picture

@app.route('/account', methods=['POST', 'GET'])
@login_required
def account():
    form=AccountUpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file=save_image(form.picture.data)
            current_user.image_file=image_file
        current_user.username=form.username.data
        current_user.email=form.email.data
        user_details=UserDetails(firstname=form.firstname.data,lastname=form.lastname.data, user_id=current_user.id)
        db.session.add(user_details)
        db.session.commit()
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
        form.firstname.data=current_user.details  # original text         form.firstname.data=current_user.details[-1].firstname
        form.lastname.data=current_user.details
    image_url=url_for('static', filename='profile_pics/'+current_user.image_file)
    return render_template('account.html', title='Account Page', legend='Account Details', form=form, image_url=image_url)

@app.route('/sign-up', methods=['POST', 'GET'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form=RegistrationForm()
    if form.validate_on_submit():
        encrypted_password=bcrypt.generate_password_hash(form.password.data).decode('utf8')
        user=User(username=form.username.data,email=form.email.data,password=encrypted_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created successfully for {form.username.data}', category='success')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Sign Up',form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('account'))
    form = LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user)
            flash(f'Login successfully for {form.email.data}', category='success')
            return redirect(url_for('account'))
        else:
            flash(f'Login Unsuccessfully for {form.email.data}', category='danger')
    return render_template('login.html', title='Login Page',form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

def send_mail(user):
    token=user.get_token()
    msg=Message('Password Reset Request', recipients=[user.email],sender='noreply@holacuenta.me')
    msg.body=f'''  You're receiving this e-mail because you requested a password reset for your user account at holacuenta.me.

    {url_for('reset_token', token=token,_external=True)}
    
    If you didn't request this change, you can disregard this email - we have not yet reset your password. 
    
    '''
    mail.send(msg)

@app.route('/reset_password', methods=['POST', 'GET'])
def reset_password():
    form=ResetPasswordForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user:
            send_mail(user)
            flash('Password Reset sent to your email. Please check your email.','success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password Page',form=form, legend='Reset Password')

@app.route('/reset_password/<token>', methods=['POST', 'GET'])
def reset_token(token):
    user=User.verify_token(token)
    if user is None:
        flash('That token is invalid or it already expired, Please try again.', 'warning')
        return redirect(url_for('reset_password'))

    form=ChangePasswordForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf8')
        user.password=hashed_password
        db.session.commit()
        flash('Password changed successfully! Please login again.', 'success')
        return redirect(url_for('login'))
    return render_template('change_password.html', title="Change Password", legend='Change Password', form=form)


######  ADDED STARTED HERE  ######

@app.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == "POST":
        text = request.form.get('text')

        if not text:
            flash('Post cannot be empty', category='error')
        else:
            post = Post(text=text, author=current_user.id)
            db.session.add(post)
            db.session.commit()
            flash('Post created!', category='success')
            return redirect(url_for('homepage'))

    return render_template('create_post.html', user=current_user)


@app.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.id:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')

    return redirect(url_for('homepage'))


@app.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('homepage'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)


@app.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty.', category='error')
    else:
        post = Post.query.filter_by(id=post_id)
        if post:
            comment = Comment(
                text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('homepage'))


@app.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist.', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('You do not have permission to delete this comment.', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('homepage'))


@app.route("/like-post/<post_id>", methods=['POST'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first()
    like = Like.query.filter_by(
        author=current_user.id, post_id=post_id).first()

    if not post:
        return jsonify({'error': 'Post does not exist.'}, 400)
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return jsonify({"likes": len(post.likes), "liked": current_user.id in map(lambda x: x.author, post.likes)})


######  ADDED ENDED HERE  ######


######  START CREATED BY ME HERE  ######

@app.route('/contact')
def contact():
    return render_template('contactus.html')



######  END CREATED BY ME HERE  ######
