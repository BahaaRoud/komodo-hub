from datetime import datetime
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Assignment, Class, SightingReport, Submission, User
from sqlalchemy.exc import SQLAlchemyError

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    print(f"Current Role: {current_user.role}")
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('common.home'))

    # Retrieve classes taught by the current teacher
    classes = Class.query.filter_by(teacher_id=current_user.id).all()

    return render_template('teacher_dashboard.html', classes=classes)


@teacher_bp.route('/classes', methods=['GET', 'POST'])
@login_required
def classes():
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('common.home'))

    # Retrieve classes taught by the current teacher
    classes = Class.query.filter_by(teacher_id=current_user.id).all()

    if request.method == 'POST':
        # Handle class creation if form data is present
        class_name = request.form.get('class_name')
        subject = request.form.get('subject')
        
        if class_name and subject:
            
            new_class = Class(name=class_name, subject=subject, teacher_id=current_user.id)
            db.session.add(new_class)
            db.session.commit()
            flash(f"Class '{class_name}' created successfully! Entry Code {new_class.entry_code}", "success")
            return redirect(url_for('teacher.classes'))
        else:
            flash("Please fill in all fields.", "danger")

    return render_template('classes.html', classes=classes)

@teacher_bp.route('/delete_class/<int:class_id>', methods=['POST'])
@login_required
def delete_class(class_id):
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('common.home'))

    class_to_delete = Class.query.get_or_404(class_id)
    if class_to_delete.teacher_id != current_user.id:
        flash("You do not have permission to delete this class.", "danger")
        return redirect(url_for('teacher.classes'))

    db.session.delete(class_to_delete)
    db.session.commit()
    flash(f"Class '{class_to_delete.name}' has been deleted.", "success")
    return redirect(url_for('teacher.classes'))

@teacher_bp.route('/class_students/<int:class_id>', methods=['GET', 'POST'])
@login_required
def class_students(class_id):
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('common.home'))

    class_ = Class.query.get_or_404(class_id)
    if class_.teacher_id != current_user.id:
        flash("You do not have permission to view this class.", "danger")
        return redirect(url_for('teacher.classes'))

    # Handle student removal if a student_id is posted
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        student_to_remove = User.query.get(student_id)
        if student_to_remove in class_.students:
            class_.students.remove(student_to_remove)
            db.session.commit()
            flash(f"Student '{student_to_remove.username}' has been removed from {class_.name}.", "success")
        else:
            flash("Student not found in this class.", "danger")

    return render_template('class_students.html', class_=class_)

@teacher_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
def assignments():
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('common.home'))

    # Retrieve assignments created by the teacher
    assignments = Assignment.query.filter_by(teacher_id=current_user.id).all()

    # Retrieve classes for assignment creation
    classes = Class.query.filter_by(teacher_id=current_user.id).all()

    if request.method == 'POST':
        # Handle assignment creation if form data is provided
        title = request.form.get('title')
        description = request.form.get('description')
        deadline_str = request.form.get('deadline')
        class_id = request.form.get('class_id')

        if not title or not description or not deadline_str or not class_id:
            flash('All fields are required', 'danger')
            return redirect(url_for('teacher.assignments'))
        
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            class_id = int(class_id)
            new_assignment = Assignment(
                title=title,
                description=description,
                deadline=deadline,
                teacher_id=current_user.id,
                class_id=class_id
            )
            db.session.add(new_assignment)
            db.session.commit()
            flash('Assignment created successfully!', 'success')
        except ValueError as ve:
            flash("Invalid date format or class selected.", 'danger')
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Database error: {str(e)}", "danger")

        return redirect(url_for('teacher.assignments'))

    return render_template('assignments.html', assignments=assignments, classes=classes)

@teacher_bp.route('/manage_assignments', methods=['GET'])
@login_required
def manage_assignments():
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('teacher.teacher_dashboard'))

    # Get all classes taught by the current teacher
    classes = Class.query.filter_by(teacher_id=current_user.id).all()

    # Structure data to hold classes with their assignments and submissions
    classes_data = []
    for class_ in classes:
        assignments = Assignment.query.filter_by(class_id=class_.id).all()
        
        assignment_data = []
        for assignment in assignments:
            # Fetch all submissions for each assignment
            submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
            assignment_data.append({'assignment': assignment, 'submissions': submissions})
        
        classes_data.append({'class': class_, 'assignments': assignment_data})

    return render_template('manage_assignments.html', classes_data=classes_data)

@teacher_bp.route('/manage_reports', methods=['GET', 'POST'])
@login_required
def manage_reports():
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('common.home'))

    # Retrieve all classes taught by the current teacher
    teacher_classes = Class.query.filter_by(teacher_id=current_user.id).all()

    # Get all students in these classes
    student_ids = [student.id for class_ in teacher_classes for student in class_.students]

    # Fetch unique sighting reports from these students
    sightings = SightingReport.query.filter(SightingReport.user_id.in_(student_ids)).distinct().all()

    if request.method == 'POST':
        report_id = request.form.get('report_id')
        action = request.form.get('action')

        sighting = SightingReport.query.get_or_404(report_id)

        if sighting.user_id not in student_ids:
            flash("You dont have permission to modify this report", "danger")
            return redirect(url_for('teacher.manage_reports'))
        
        if action == 'delete':
            db.session.delete(sighting)
            db.session.commit()
            flash("Sighting Report deleted successfully", "success")
        elif action == 'feedback':
            feedback = request.form.get('feedback')
            if feedback:
                sighting.feedback = feedback
                db.session.commit()
                flash("Feedback Submitted Successfully", "success")
        else: 
            redirect(url_for('teacher.manage_reports'))

    return render_template('manage_reports.html', sightings=sightings)


@teacher_bp.route('/create_assignment', methods=['GET', 'POST'])
@login_required
def create_assignment():
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('common.home'))

    # Retrieve classes taught by the current teacher
    classes = Class.query.filter_by(teacher_id=current_user.id).all()

    organization_id = current_user.organization_id

    print(f"Classes for teacher {current_user.username}: {[c.name for c in classes]}")

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        deadline_str = request.form.get('deadline')
        class_id = request.form.get('class_id')  # Retrieve selected class ID

        print(f"Received data: title={title}, description={description}, deadline={deadline_str}, class_id={class_id}")

        if not title or not description or not deadline_str or not class_id:
            flash('All fields are required', 'danger')
            return redirect(url_for('teacher.create_assignment'))
        
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            class_id = int(class_id)
            new_assignment = Assignment(
                title=title,
                description=description,
                deadline=deadline,
                teacher_id=current_user.id,
                class_id=class_id,  # Associate assignment with the selected class
                organization_id=organization_id
            )

            db.session.add(new_assignment)
            db.session.commit()

            print(f"New assignment created: {new_assignment.title} for class_id: {new_assignment.class_id}")
            
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('teacher.teacher_dashboard'))
        
        except ValueError as ve:
            print(f"ValueError: {ve}")  # Debugging
            flash("Invalid date format or class selected.", 'danger')
            return redirect(url_for('teacher.create_assignment'))
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"SQLAlchemyError: {e}")  # Debugging
            flash(f"Database error: {str(e)}", "danger")
            return redirect(url_for('teacher.create_assignment'))
    return render_template('create_assignment.html', classes=classes)

@teacher_bp.route('/delete_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('teacher.teacher_dashboard'))

    assignment = db.session.get(Assignment, assignment_id)
    if not assignment or assignment.teacher_id != current_user.id:
        flash("You do not have permission to delete this assignment.", "danger")
        return redirect(url_for('teacher.assignments'))

    db.session.delete(assignment)
    db.session.commit()
    flash(f"Assignment '{assignment.title}' has been deleted.", "success")
    return redirect(url_for('teacher.assignments'))


@teacher_bp.route('/toggle_assignment_status/<int:assignment_id>', methods=['POST'])
@login_required
def toggle_assignment_status(assignment_id):
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('teacher.teacher_dashboard'))

    assignment = db.session.get(Assignment, assignment_id)
    if not assignment or assignment.teacher_id != current_user.id:
        flash("You do not have permission to modify this assignment.", "danger")
        return redirect(url_for('teacher.assignments'))

    # Toggle the is_closed status
    assignment.is_closed = not assignment.is_closed
    db.session.commit()

    status = "closed" if assignment.is_closed else "open"
    flash(f"Assignment '{assignment.title}' submissions are now {status}.", "success")
    return redirect(url_for('teacher.assignments'))


@teacher_bp.route('/add_feedback/<int:submission_id>', methods=['POST'])
@login_required
def add_feedback(submission_id):
    if current_user.role != 'Teacher':
        flash("Access restricted to teachers only.", "danger")
        return redirect(url_for('teacher.teacher_dashboard'))

    submission = db.session.get(Submission, submission_id)
    if submission is None:
        abort(404)
    
    # Check if the teacher owns this assignment
    if submission.related_assignment.teacher_id != current_user.id:
        flash("You do not have permission to grade this submission.", "danger")
        return redirect(url_for('teacher.teacher_dashboard'))

    # Get feedback from form
    feedback = request.form.get('feedback')
    if feedback:
        submission.feedback = feedback
        db.session.commit()
        flash("Feedback submitted successfully.", "success")
    else:
        flash("Feedback cannot be empty.", "danger")

    return redirect(url_for('teacher.manage_assignments'))

@teacher_bp.route('/toggle_student_sighting_privacy/<int:sighting_id>', methods=['POST'])
@login_required
def toggle_student_sighting_privacy(sighting_id):
    if current_user.role != "Teacher":
        abort(403)

    sighting = SightingReport.query.get_or_404(sighting_id)

    # Check if the sighting belongs to a student under the teacher
    student_ids = [
        student.id
        for class_ in Class.query.filter_by(teacher_id=current_user.id).all()
        for student in class_.students
    ]
    if sighting.user_id not in student_ids:
        abort(403)

    # Toggle the privacy
    sighting.is_public = not sighting.is_public
    db.session.commit()
    flash("Sighting privacy updated!", "success")
    return redirect(url_for('teacher.manage_reports'))


