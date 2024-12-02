from flask import Blueprint, abort, jsonify, render_template, redirect, url_for, flash, request, current_app as app
from flask_login import login_required, current_user, login_user, logout_user
from models import Class, Message, Organization, Post, SightingReport, User, Role
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash

common_bp = Blueprint('common', __name__)


@common_bp.app_template_filter('has_role')
def has_role(user, role_name):
    return any(role.name == role_name for role in user.roles)


@common_bp.route('/')
def home():
    user_role = current_user.role if current_user.is_authenticated else None
    print(user_role)
    return render_template('home.html', user_role=user_role)

@common_bp.route('/register_user', methods = ['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        data = request.get_json()
        print("Recieved Data:", data)

        # User registration details
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        organization_code = data.get('organization_code')
        access_code = data.get('accessCode')

        if not all([username, email, password, role]):
            return "Missing fields", 400 
        
        organization = Organization.query.filter_by(org_code=organization_code).first()

        if organization is None and role != "Community Member":
            flash("Invalid organization code.", "danger")
            return jsonify({'message': "Missing required fields"}), 400

        # Validate role and access code
        if organization:
            if organization.org_type == "School":
                if role == "Admin" and access_code != organization.admin_access_code:
                    return jsonify({'message': "Invalid access code for Admin role"}), 400
                elif role == "Teacher" and access_code != organization.teacher_access_code:
                     return jsonify({'message': "Invalid access code for Teacher role"}), 400
                elif role == "Student" and access_code != organization.student_access_code:
                    return jsonify({'message': "Invalid access code for Student role"}), 400
            elif organization.org_type == "General Org":
                if role == "Admin" and access_code != organization.admin_access_code:
                    return jsonify({'message': "Invalid access code for Admin role"}), 400
                elif role == "User" and access_code != organization.user_access_code:
                    return jsonify({'message': "Invalid access code for User role"}), 400

        # Save the user to the database
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role=role,
            organization_id=organization.id if organization else None
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': "User Registered Successfully!"}), 200

    return render_template('register_user.html')

@common_bp.route('/register_organization', methods=['GET', 'POST'])
def register_organization():
    if request.method == 'POST':
        org_name = request.form.get('org_name')
        org_type = request.form.get('org_type')
        admin_email = request.form.get('admin_email')
        admin_password = request.form.get('admin_password')

        existing_organization = Organization.query.filter_by(name=org_name).first()
        if existing_organization:
            flash(f"Organization '{org_name}' already exists. Please choose a different name.", "danger")
            return redirect(url_for('common.register_organization'))

        # Create the new organization
        new_org = Organization(name=org_name, org_type=org_type)
        db.session.add(new_org)
        db.session.commit()

        # Ensure "Admin" role exists in the Role table
        admin_role = Role.query.filter_by(name="Admin").first()
        if not admin_role:
            admin_role = Role(name="Admin")
            db.session.add(admin_role)
            db.session.commit()

        # Create the admin user for this organization
        admin_user = User(  
            username=admin_email.split('@')[0],  # Example username based on email
            email=admin_email,
            password=generate_password_hash(admin_password),
            organization_id=new_org.id,
            role="Admin"
        )
        # Assign the "Admin" role to the new user
        admin_user.roles.append(admin_role)

        # Commit the new user to the database
        db.session.add(admin_user)
        db.session.commit()

        flash('Organization registered successfully with an admin account!', 'success')

        # Show access codes based on organization type
        if new_org.org_type == "School":
            access_codes = {
                "Organization Code": new_org.org_code,
                "Admin Code": new_org.admin_access_code,
                "Teacher Code": new_org.teacher_access_code,
                "Student Code": new_org.student_access_code
            }
            return render_template('login.html', access_codes=access_codes)
        elif new_org.org_type == "General Org":
            access_codes = {
                "Organization Code": new_org.org_code,
                "Admin Code": new_org.admin_access_code,
                "User Code": new_org.user_access_code
            }
            return render_template('login.html', access_codes=access_codes)

    return render_template('register_organization.html')

@common_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already logged in', 'info')
        return redirect(url_for('common.home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('common.home'))
        else: 
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@common_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('common.login'))

@common_bp.route('/about')
def about():
    return render_template('about.html')

@common_bp.route('/contact')
def contact():
    return render_template('contact.html')

@common_bp.route('/submit_contact', methods=['POST'])
def submit_contact():
    return render_template('contact_success.html')

@common_bp.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@common_bp.route('/messages', methods=['GET', 'POST'])
@login_required
def inbox():
    if current_user.role == 'Teacher':
        # Teachers can only chat with students they teach
        student_ids = [
            student.id
            for class_ in Class.query.filter_by(teacher_id=current_user.id).all()
            for student in class_.students
        ]
        conversations = User.query.filter(
            (User.id.in_(student_ids)) & (User.id != current_user.id)
        ).all()
    elif current_user.role == 'Student':
        # Students can only chat with their teachers
        teacher_ids = [
            class_.teacher_id for class_ in current_user.enrolled_classes
        ]
        conversations = User.query.filter(
            (User.id.in_(teacher_ids)) & (User.id != current_user.id)
        ).all()
    else:
        conversations = []  # For other user types, no conversations available

    if request.method == 'POST':
        recipient_username = request.form.get('username')
        recipient = User.query.filter_by(username=recipient_username).first()

        if not recipient or recipient.id == current_user.id:
            flash("Invalid user or you cannot chat with yourself.", "danger")
            return redirect(url_for('common.inbox'))

        return redirect(url_for('common.chat', recipient_username=recipient.username))

    return render_template('inbox.html', conversations=conversations)

# Chat Route
@common_bp.route('/messages/<string:recipient_username>', methods=['GET', 'POST'])
@login_required
def chat(recipient_username):
    recipient = User.query.filter_by(username=recipient_username).first()
    if not recipient:
        flash("User not found.", "danger")
        return redirect(url_for('common.inbox'))

    # Permission check: Teachers can only message students they teach, and students can only message their teachers
    if current_user.role == 'Teacher':
        student_ids = [student.id for class_ in Class.query.filter_by(teacher_id=current_user.id) for student in class_.students]
        if recipient.id not in student_ids:
            flash("You can only chat with students in your classes.", "danger")
            return redirect(url_for('common.inbox'))
    elif current_user.role == 'Student':
        teacher_ids = [class_.teacher_id for class_ in current_user.enrolled_classes]
        if recipient.id not in teacher_ids:
            flash("You can only chat with teachers of your classes.", "danger")
            return redirect(url_for('common.inbox'))

    # Post a new message
    if request.method == 'POST':
        message_text = request.form.get('message')
        if message_text:
            new_message = Message(
                sender_id=current_user.id,
                recipient_id=recipient.id,
                message_text=message_text
            )
            db.session.add(new_message)
            db.session.commit()
            flash("Message sent!", "success")
        else:
            flash("Message cannot be empty.", "danger")

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient.id)) |
        ((Message.sender_id == recipient.id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp).all()

    return render_template('chat.html', recipient=recipient, messages=messages)

@common_bp.route('/start_conversation', methods=['POST'])
@login_required
def start_conversation():
    username = request.form.get('username')
    recipient = User.query.filter_by(username=username).first()

    if not recipient:
        flash("User not found.", "danger")
        return redirect(url_for('common.inbox'))

    # Check if a conversation already exists by searching for messages
    existing_messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == recipient.id)) |
        ((Message.sender_id == recipient.id) & (Message.recipient_id == current_user.id))
    ).first()

    # Redirect to existing conversation if messages exist
    if existing_messages:
        return redirect(url_for('common.chat', recipient_username=recipient.username))

    # Check permissions
    if current_user.role == 'Teacher':
        student_ids = [student.id for class_ in Class.query.filter_by(teacher_id=current_user.id) for student in class_.students]
        if recipient.id not in student_ids:
            flash("You can only message students in your classes.", "danger")
            return redirect(url_for('common.inbox'))
    elif 'Student' in [role.name for role in current_user.roles]:
        teacher_ids = [class_.teacher_id for class_ in current_user.classes]
        if recipient.id not in teacher_ids:
            flash("You can only message teachers of your classes.", "danger")
            return redirect(url_for('common.inbox'))

    # No conversation exists, but permissions are valid
    # Start a new conversation by redirecting to the chat page
    return redirect(url_for('common.chat', recipient_username=recipient.username))

@common_bp.route('/toggle_post_privacy/<int:post_id>', methods=['POST'])
@login_required
def toggle_post_privacy(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and current_user.role != "Admin":
        abort(403)

    post.is_public = not post.is_public
    db.session.commit()
    flash("Post privacy updated!", "success")
    return redirect(url_for('org_user.org_user_library'))

@common_bp.route('/toggle_sighting_privacy/<int:sighting_id>', methods=['POST'])
@login_required
def toggle_sighting_privacy(sighting_id):
    sighting = SightingReport.query.get_or_404(sighting_id)

    allowed_roles = ["Admin", "Teacher"]
    if sighting.user_id != current_user.id and current_user.role not in allowed_roles:
        abort(403)

    sighting.is_public = not sighting.is_public
    db.session.commit()
    flash("Sighting privacy updated!", "success")
    return redirect(url_for('teacher.manage_reports'))


@common_bp.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and current_user.role != "Admin":
        abort(403)

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted!", "success")
    return redirect(url_for('org_user.org_user_library'))

@common_bp.route('/delete_sighting/<int:sighting_id>', methods=['POST'])
@login_required
def delete_sighting(sighting_id):
    sighting = SightingReport.query.get_or_404(sighting_id)
    if sighting.user_id != current_user.id and current_user.role != "Admin":
        abort(403)

    db.session.delete(sighting)
    db.session.commit()
    flash("Sighting deleted!", "success")
    return redirect(url_for('org_user.org_user_library'))

@common_bp.route('/public_library', methods = ['GET'])
def public_library():

    org_filter = request.args.get('org', 'all')
    content_filter = request.args.get('type', 'all')

    posts_query = Post.query.filter(Post.is_public == True)
    sightings_query = SightingReport.query.filter(SightingReport.is_public)

    if org_filter == 'School':
        posts_query = posts_query.join(Organization).filter(Organization.org_type == 'School')
        sightings_query = sightings_query.join(Organization).filter(Organization.org_type == 'School')
    elif org_filter == 'General Org':
        posts_query = posts_query.join(Organization).filter(Organization.org_type == 'General Org')
        sightings_query = sightings_query.join(Organization).filter(Organization.org_type == 'General Org')
    elif org_filter == 'no_org':
        posts_query = posts_query.filter(Post.organization_id == None)
        sightings_query = sightings_query.filter(SightingReport.organization_id == None)

    posts = []
    sightings = []
    if content_filter in ('posts', 'both'):
        posts = posts_query.all()
    if content_filter in ('sightings', 'both'):
        sightings = sightings_query.all()

    return render_template('public_library.html', posts=posts, sightings=sightings, org_filter=org_filter, content_filter=content_filter)