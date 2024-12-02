import os
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Assignment, Class, SightingReport, Submission
from werkzeug.utils import secure_filename
from flask import current_app as app

student_bp = Blueprint('student', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@student_bp.route('/student_dashboard')
@login_required
def student_dashboard():
    
    if current_user.role!= 'Student':
        flash("Access restricted to students only.", "danger")
        return redirect(url_for('common.home'))
    return render_template('student_dashboard.html')

@student_bp.route('/join_class', methods=['GET', 'POST'])
@login_required
def join_class():
    if current_user.role!= 'Student':
        flash("Access restricted to students only.", "danger")
        return redirect(url_for('student.student_dashboard'))

    if request.method == 'POST':
        entry_code = request.form.get('entry_code')
        target_class = Class.query.filter_by(entry_code=entry_code).first()

        if target_class:
            if current_user not in target_class.students:
                target_class.students.append(current_user)
                db.session.commit()
                flash(f"Successfully joined {target_class.name}!", "success")
            else:
                flash("You are already enrolled in this class.", "info")
            return redirect(url_for('student.student_dashboard'))
        else:
            flash("Invalid entry code. Please try again.", "danger")

    return render_template('join_class.html')

@student_bp.route('/species_sightings', methods=['GET', 'POST'])
@login_required
def species_sightings():
    if current_user.role!= 'Student':
        flash("Access restricted to students only.", "danger")
        return redirect(url_for('common.home'))
    
    sighting_reports = SightingReport.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        description = request.form.get('description')
        location = request.form.get('location')
        photo_file = request.files.get('photo')

        if not description or not location:
            flash("Description and location are required.", "danger")
            return redirect(url_for('student.species_sightings'))

        photo_filename = None
        if photo_file and allowed_file(photo_file.filename):
            photo_filename = secure_filename(photo_file.filename)
            photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

        new_report = SightingReport(
            description=description,
            location=location,
            photo=photo_filename,
            user_id=current_user.id,
            organization_id=current_user.organization_id
        )

        db.session.add(new_report)
        db.session.commit()
        
        flash("Sighting report submitted successfully!", "success")
        return redirect(url_for('student.species_sightings'))

    return render_template('species_sightings.html', sighting_reports=sighting_reports)

@student_bp.route('/student_assignments', methods=['GET'])
@login_required
def student_assignments():
    if current_user.role!= 'Student':
        flash("Access restricted to students only.", "danger")
        return redirect(url_for('common.home'))

    organization_id = current_user.organization_id

    # Get the classes the student is enrolled in
    enrolled_classes = current_user.enrolled_classes

    # Get assignments for each enrolled class along with submission status
    assignments_data = []
    for class_ in enrolled_classes:
        class_assignments = []
        
        for assignment in Assignment.query.filter_by(class_id=class_.id, organization_id=organization_id).all():
            # Check if the student has already submitted this assignment
            submission = Submission.query.filter_by(assignment_id=assignment.id, student_id=current_user.id).first()
            class_assignments.append({
                'assignment': assignment,
                'submitted': submission is not None,  # True if a submission exists
                'submission': submission  # Pass the submission object if it exists
            })
        
        assignments_data.append({'class': class_, 'assignments': class_assignments})

    return render_template('student_assignments.html', assignments_data=assignments_data)

@student_bp.route('/submit_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    if current_user.role!= 'Student':
        flash("Access restricted to students only.", "danger")
        return redirect(url_for('common.home'))

    assignment = Assignment.query.get_or_404(assignment_id)

    organization_id = current_user.organization_id

    # Check if assignment is open for submissions
    if assignment.is_closed:
        flash("Submissions are closed for this assignment.", "danger")
        return redirect(url_for('student.student_assignments'))

    # Check for duplicate submission
    existing_submission = Submission.query.filter_by(assignment_id=assignment.id, student_id=current_user.id).first()
    if existing_submission:
        flash("You have already submitted this assignment.", "warning")
        return redirect(url_for('student.student_assignments'))

    content = request.form.get('content')
    file = request.files.get('file')
    file_path = None

    # Handle file upload if present
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(file_path)

            file_path = f'uploads/{filename}'
        except Exception as e:
            flash(f"File upload failed: {e}", "danger")
            return redirect(url_for('student.student_assignments'))

    # Ensure submission is not empty
    if not content and not file:
        flash("You must provide either content or upload a file.", "danger")
        return redirect(url_for('student.student_assignments'))

    # Create a new submission
    new_submission = Submission(
        content=content,
        file_path=file_path,
        assignment_id=assignment.id,
        student_id=current_user.id,
        organization_id=organization_id
    )

    db.session.add(new_submission)
    db.session.commit()
    flash("Assignment submitted successfully!", "success")
    return redirect(url_for('student.student_assignments'))



@student_bp.route('/student_library')
@login_required
def student_library():
    if current_user.role!= 'Student':
        flash("Access restricted to students only.", "danger")
        return redirect(url_for('common.home'))

    # Fetch the student's submissions and sightings
    submissions = Submission.query.filter_by(student_id=current_user.id).all()
    sightings = SightingReport.query.filter_by(user_id=current_user.id).all()

    return render_template('student_library.html', submissions=submissions, sightings=sightings)