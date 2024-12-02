from functools import wraps
from flask import Blueprint, abort, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Post, User, Organization, SightingReport, Class, Activity
from extensions import db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Admin':
            abort(403)  # Forbidden error
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@admin_bp.route('/manage_users')
@login_required
@admin_required
def manage_users():
    users = User.query.filter_by(organization_id=current_user.organization_id).all()
    for user in users:
        print(f"User: {user.username}, Role: {user.role}")
    return render_template('manage_users.html', users=users)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        abort(404)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted Successfully!', 'success')
    return redirect(url_for('manage_users'))

@admin_bp.route('/content_management')
@login_required
@admin_required
def content_management():

    posts = Post.query.filter_by(organization_id=current_user.organization_id).all()

    sightings = SightingReport.query.filter_by(organization_id=current_user.organization_id).all()

    return render_template('content_management.html', posts=posts, sightings=sightings)

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    # Example analytics data
    org_id = current_user.organization_id

    user_count = User.query.filter_by(organization_id=org_id).count()
    sighting_count = SightingReport.query.filter_by(organization_id=org_id).count()
    class_count = Class.query.join(User, Class.teacher_id == User.id).filter(User.organization_id == org_id).count()
    activity_count = Activity.query.join(User, Activity.user_id == User.id).filter(User.organization_id == org_id).count()

    users = User.query.filter_by(organization_id=org_id).all()
    classes = Class.query.filter_by(organization_id=org_id).all()

    analytics_data = {
        'user_count': user_count,
        'sighting_count': sighting_count,
        'class_count': class_count,
        'activity_count': activity_count
    }
    return render_template('analytics.html', **analytics_data, users=users, classes=classes)

@admin_bp.route('/org_access_codes/<int:org_id>')
@login_required
@admin_required
def org_access_codes(org_id):
    org = Organization.query.get_or_404(org_id)
    org_data = {
        "org_name": org.name,
        "org_code": org.org_code,
        "admin_code": org.admin_access_code
    }
    if org.org_type == 'School':
        org_data.update({
            "teacher_code": org.teacher_access_code,
            "student_code": org.student_access_code,
            "org_type": "School"
        })
    elif org.org_type == 'General Org':
        org_data.update({
            "user_code": org.user_access_code,
            "org_type": "General Org"
        })
        print(org.user_access_code)
    return render_template('org_access_codes.html', **org_data)
