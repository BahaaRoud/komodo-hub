import os
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from flask import current_app as app
from extensions import db
from models import Post, SightingReport

org_user_bp = Blueprint('org_user', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@org_user_bp.route('/org_user_dashboard', methods=['GET'])
@login_required
def org_user_dashboard():
    # Fetch user-specific data
    user_posts_count = Post.query.filter_by(user_id=current_user.id).count()
    user_sightings_count = SightingReport.query.filter_by(user_id=current_user.id).count()

    return render_template(
        'org_user_dashboard.html',
        user_posts_count=user_posts_count,
        user_sightings_count=user_sightings_count
    )



@org_user_bp.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        link = request.form.get('link')
        photo_file = request.files.get('photo')
        file = request.files.get('file')

        # Handle file and photo uploads
        photo_filename = None
        if photo_file and allowed_file(photo_file.filename):
            photo_filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        file_filename = None
        if file:
            file_filename = secure_filename(file.filename)
            #file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_filename))

        # Create a new Post object
        post = Post(
            title=title,
            content=content,
            link=link,
            photo=photo_filename,
            file_path=file_filename,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )

        db.session.add(post)
        db.session.commit()
        flash("Post created successfully!", "success")
        return redirect(url_for('org_user.org_user_library'))

    return render_template('create_post.html')

@org_user_bp.route('/org_user_report_sighting', methods=['GET', 'POST'])
@login_required
def org_user_report_sighting():
    if request.method == 'POST':
        description = request.form.get('description')
        location = request.form.get('location')
        photo_file = request.files.get('photo')

        # Handle photo upload
        photo_filename = None
        if photo_file and allowed_file(photo_file.filename):
            photo_filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        # Create a new SightingReport object
        sighting = SightingReport(
            description=description,
            location=location,
            photo=photo_filename,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )

        db.session.add(sighting)
        db.session.commit()
        flash("Sighting reported successfully!", "success")
        return redirect(url_for('org_user.org_user_library'))

    return render_template('org_user_report_sighting.html')

@org_user_bp.route('/org_user_library', methods=['GET'])
@login_required
def org_user_library():
    # Fetch posts: Either public or created by the current user
    posts = Post.query.filter(
        (Post.user_id == current_user.id) &
        (Post.organization_id == current_user.organization_id)
    ).distinct().all()

    # Fetch sightings: Either public or created by the current user
    sightings = SightingReport.query.filter(
        (SightingReport.user_id == current_user.id) &
        (SightingReport.organization_id == current_user.organization_id)
    ).distinct().all()

    return render_template('org_user_library.html', posts=posts, sightings=sightings)

