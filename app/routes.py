from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app
from app.models import User, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, CreateListingForm, EditListingForm, FilterForm
from datetime import datetime
from app.models import Listing, ListingTag
from app.forms import MessageForm
from app.models import Message
from app.models import Notification
from collections import OrderedDict
from sqlalchemy.sql import exists

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    tags = request.args.get('tags')
    title = request.args.get('title')
    form = FilterForm()
    if form.validate_on_submit():
        if form.filter_submit.data:
            tags = form.user_input.data.replace(" ","").lower()
            if tags == "":
                return redirect(url_for('index'))
            return redirect(url_for('index', tags=tags))
        if form.title_submit.data:
            title = form.user_input.data
            if title == "":
                return redirect(url_for('index'))
            return redirect(url_for('index', title=title))
        if form.user_submit.data:
            target_name = form.user_input.data
            user_exists = db.session.query(exists().where(User.username == target_name)).scalar()
            if user_exists:
                return redirect(url_for('user', username=target_name))
            else:
                flash('No user found with the entered username')
        if form.clear.data:
            return redirect(url_for('index'))
    results = Listing.query.filter_by(is_complete=False).order_by(Listing.timestamp.desc())
    listings = results.paginate(page, app.config['LISTINGS_PER_PAGE'], False)
    if tags is not None:
        search_tags = set(list(filter(None, tags.split('#'))))
        desired_listings = set()
        for result in results:
            found_tags = set()
            for tag in result.tags:
                found_tags.add(tag.tag)
            if search_tags.issubset(found_tags):
                desired_listings.add(result.id)
        listings = Listing.query.filter(Listing.id.in_(desired_listings)).order_by(Listing.timestamp.desc()).paginate(page, app.config['LISTINGS_PER_PAGE'], False) 
    if title is not None:
        listings = Listing.query.filter(Listing.title.contains(title)).order_by(Listing.timestamp.desc()).paginate(page, app.config['LISTINGS_PER_PAGE'], False)
    next_url = url_for('index', page=listings.next_num, tags=tags, title=title) \
        if listings.has_next else None
    prev_url = url_for('index', page=listings.prev_num, tags=tags, title=title) \
        if listings.has_prev else None
    return render_template('index.html', title='Home', listings=listings.items, next_url=next_url, prev_url=prev_url, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, major=form.major.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Welcome, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    lpage = request.args.get('lpage', 1, type=int)
    rpage = request.args.get('rpage', 1, type=int)
    desired_ids = set()
    for listing in user.joined_listing:
        desired_ids.add(listing.id)
    user_listings = Listing.query.filter(Listing.id.in_(desired_ids))
    curr_listings = user_listings.filter_by(is_complete=False).order_by(Listing.timestamp.desc()).paginate(lpage, app.config['LISTINGS_PER_PAGE']/2, False)
    comp_listings = user_listings.filter_by(is_complete=True).order_by(Listing.timestamp.desc()).paginate(rpage, app.config['LISTINGS_PER_PAGE']/2, False)
    curr_next_url = url_for('user', username=user.username, lpage=curr_listings.next_num, rpage=comp_listings.page) \
        if curr_listings.has_next else None
    curr_prev_url = url_for('user', username=user.username, lpage=curr_listings.prev_num, rpage=comp_listings.page) \
        if curr_listings.has_prev else None
    comp_next_url = url_for('user', username=user.username, lpage=curr_listings.page, rpage=comp_listings.next_num) \
        if comp_listings.has_next else None
    comp_prev_url = url_for('user', username=user.username, lpage=curr_listings.page, rpage=comp_listings.prev_num) \
        if comp_listings.has_prev else None
    return render_template('user.html', user=user, curr_listings=curr_listings.items, curr_next_url=curr_next_url, curr_prev_url=curr_prev_url, comp_listings=comp_listings.items, comp_next_url=comp_next_url, comp_prev_url=comp_prev_url)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/create_listing', methods=['GET', 'POST'])
@login_required
def create_listing():
    form = CreateListingForm()
    if form.validate_on_submit():
        listing = Listing(title=form.title.data, body=form.body.data, desired_size=form.desired_size.data, owner=current_user)
        tags = form.tags.data
        tags = tags.replace(" ","").lower().split('#')
        tags = list(OrderedDict.fromkeys(filter(None, tags)))
        for _tag in tags:
            tag = ListingTag.query.filter_by(tag=_tag).first()
            if tag is None:
                tag=ListingTag(tag=_tag)
            listing.tags.append(tag)
        listing.members.append(current_user)
        db.session.add(listing)
        db.session.commit()
        flash('Your listing is now posted!')
        return redirect(url_for('index'))
    return render_template('create_listing.html', title='Create a Listing', form=form)

@app.route('/view_listing/<listing_id>', methods=['GET', 'POST'])
@login_required
def view_listing(listing_id):
    form = EditListingForm()
    listing = Listing.query.filter_by(id=listing_id).first_or_404()
    if listing.is_complete == True:
        del form.complete_project
    if current_user.id is not listing.owner.id:
        del form.complete_project
        del form.delete_project
    else:
        del form.leave_project
    if current_user in listing.members:
        del form.join_project
    else:
        del form.leave_project 
    if form.validate_on_submit():
        if not listing.is_complete and form.complete_project is not None and form.complete_project.data:
            setattr(listing, 'is_complete', True)
            db.session.commit()
        if form.delete_project is not None and form.delete_project.data:
            listing.tags.clear()    
            listing.members.clear()
            Listing.query.filter_by(id=listing_id).delete() # TODO: can I use listing.delete() instead?
            db.session.commit()
        if form.join_project is not None and form.join_project.data:
            if current_user not in listing.members:
                listing.members.append(current_user)
                db.session.commit()
                flash('A request to join the project has been sent (actually autojoined).')
        if form.leave_project is not None and form.leave_project.data:
            if current_user in listing.members:
                listing.members.remove(current_user)
                db.session.commit()
                flash('You have been removed from the project.')
        return redirect(url_for('index'))
    return render_template('view_listing.html', listing=listing, form=form)

@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(sender=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('user', username=recipient))
    return render_template('send_message.html', title='Send Message',
                           form=form, recipient=recipient)

@app.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, app.config['LISTINGS_PER_PAGE'], False)
    next_url = url_for('messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@app.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    return jsonify([{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications])