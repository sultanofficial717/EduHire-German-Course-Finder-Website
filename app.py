from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_required, LoginManager, UserMixin, login_user
from datetime import datetime
import os
from sqlalchemy import or_, cast, Float

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'coursefinder.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'

# Initialize database
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):  # Inherit UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(80))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # <-- Add this line
    saved_programs = db.relationship('UserProgram', back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # <-- Add this line
    name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120))
    website = db.Column(db.String(120))
    programs = db.relationship('Program', backref='university', lazy=True)

class FieldOfStudy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    programs = db.relationship('Program', backref='field_of_study', lazy=True)

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'))
    field_of_study_id = db.Column(db.Integer, db.ForeignKey('field_of_study.id'))
    url = db.Column(db.String(120))
    description = db.Column(db.Text)
    ielts = db.Column(db.String(10))  # <-- Add this line
    degree_type = db.Column(db.String(50))  # <-- New column
    duration = db.Column(db.String(50))  # <-- New column
    user_programs = db.relationship('UserProgram', back_populates='program')

class UserProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
    user = db.relationship('User', back_populates='saved_programs')
    program = db.relationship('Program', back_populates='user_programs')

# Dummy user data for fallback
users = {
    "talha717": {
        "password": generate_password_hash("125taa"),
        "name": "Talha"
    },
    "guest": {
        "password": generate_password_hash("guest123"),
        "name": "Guest User"
    }
}

# Initialize database and sample data
def init_db():
    with app.app_context():
        db.create_all()

        # Add default admin if it doesn't exist
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", name="Administrator", role="admin")
            admin.set_password("admin123")  # Change this for production!
            db.session.add(admin)
            db.session.commit()

        # Add sample data if tables are empty
        if University.query.count() == 0:
            # Sample universities
            uni1 = University(name="Technical University of Munich", location="Munich, Germany", website="https://www.tum.de")
            uni2 = University(name="University of Stuttgart", location="Stuttgart, Germany", website="https://www.uni-stuttgart.de")
            uni3 = University(name="RWTH Aachen", location="Aachen, Germany", website="https://www.rwth-aachen.de")

            db.session.add_all([uni1, uni2, uni3])

            # Sample fields of study
            cs = FieldOfStudy(name="Computer Science")
            eng = FieldOfStudy(name="Engineering")
            math = FieldOfStudy(name="Mathematics")

            db.session.add_all([cs, eng, math])
            db.session.commit()

            # Add sample programs with all fields
            if Program.query.count() == 0:
                uni = University.query.first()
                field = FieldOfStudy.query.first()
                
                if uni and field:
                    programs = [
                        Program(
                            name="Computer Science Master", 
                            university_id=uni.id, 
                            field_of_study_id=field.id, 
                            ielts="6.5",
                            degree_type="Master",
                            duration="2 years",
                            description="Advanced computer science program",
                            url="https://example.com"
                        ),
                        Program(
                            name="Engineering Bachelor", 
                            university_id=uni.id, 
                            field_of_study_id=field.id, 
                            ielts="6.0",
                            degree_type="Bachelor",
                            duration="3 years",
                            description="Undergraduate engineering program",
                            url="https://example.com"
                        ),
                    ]
                    db.session.add_all(programs)
                    db.session.commit()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_saved_programs_for_user(user_id):
    user_programs = UserProgram.query.filter_by(user_id=user_id).all()
    return [up.program for up in user_programs]

# Routes
@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "user")  # Default to 'user' if not provided
        remember = True if request.form.get("remember") else False

        # Check database first
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if user.role != role:
                flash(f"Please login as {user.role}", "danger")
                return redirect(url_for("login"))

            login_user(user, remember=remember)  # <-- Add this line
            session["user"] = username
            session["user_id"] = user.id
            session["role"] = user.role
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard" if user.role == "admin" else "landing"))
        # Fallback to dummy users
        elif username in users and check_password_hash(users[username]["password"], password):
            if role != "user":
                flash("Dummy users can only login as regular users", "warning")
                return redirect(url_for("login"))

            session["user"] = username
            session["user_id"] = None  # No DB user ID for dummy users
            session["role"] = "user"
            flash("Login successful!", "success")
            return redirect(url_for("landing"))
        else:
            flash("Invalid username or password.", "danger")

    # Clear flash messages on GET request
    if request.method == "GET":
        session.pop('_flashes', None)

    return render_template("login.html")

@app.route("/landing")
@login_required
def landing():
    saved_programs = get_saved_programs_for_user(current_user.id)
    return render_template(
        'landing.html',
        user=current_user,
        username=current_user.username,
        saved_programs=saved_programs,
        now=datetime.utcnow
    )

@app.route('/admin/add_university', methods=['GET', 'POST'])
def add_university():
    if "user" not in session or session.get("role") != "admin":
        flash("Admin access required", "danger")
        return redirect(url_for("login"))
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        website = request.form['website']
        uni = University(name=name, location=location, website=website)
        db.session.add(uni)
        db.session.commit()
        flash('University added!', 'success')
        return redirect(url_for('universities'))
    return render_template('add_university.html')

@app.route('/courses')
@login_required
def courses():
    # Get filter parameters from request (degree_type and duration removed)
    search_query = request.args.get('search', '')
    field_filter = request.args.get('field', '')
    university_filters = request.args.getlist('university')
    location_filters = request.args.getlist('location')
    field_checkbox_filters = request.args.getlist('field_checkbox')
    ielts_filters = request.args.getlist('ielts')

    # Start with base query
    query = Program.query.join(University).join(FieldOfStudy)

    # Apply filters if they exist (degree_type and duration filters removed)
    if search_query:
        query = query.filter(
            or_(
                Program.name.ilike(f'%{search_query}%'),
                Program.description.ilike(f'%{search_query}%'),
                University.name.ilike(f'%{search_query}%')
            )
        )

    if field_filter:
        query = query.filter(FieldOfStudy.name == field_filter)

    if university_filters:
        query = query.filter(University.name.in_(university_filters))

    if location_filters:
        query = query.filter(University.location.in_(location_filters))

    if field_checkbox_filters:
        query = query.filter(FieldOfStudy.name.in_(field_checkbox_filters))

    if ielts_filters:
        # Convert to float for comparison, skip non-numeric (like "No IELTS Required")
        ielts_values = []
        for score in ielts_filters:
            try:
                ielts_values.append(float(score))
            except ValueError:
                pass
        # Create a list of conditions for each IELTS score
        conditions = []
        for score in ielts_values:
            conditions.append(cast(Program.ielts, Float) >= score)
        if conditions:
            query = query.filter(or_(*conditions))
        # Also allow "No IELTS Required" as a filter
        if "No IELTS Required" in ielts_filters:
            query = query.filter(or_(Program.ielts == "No IELTS Required", Program.ielts == None, Program.ielts == ""))

    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Execute query with pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    courses = pagination.items

    # Get all distinct values for filters (degree_types and durations removed)
    universities = University.query.order_by(University.name).all()
    fields = FieldOfStudy.query.order_by(FieldOfStudy.name).all()
    locations = db.session.query(University.location.distinct()).order_by(University.location).all()
    locations = [loc[0] for loc in locations if loc[0]]  # Extract from tuple

    # Get distinct IELTS scores from the database
    ielts_scores = db.session.query(Program.ielts.distinct()).filter(Program.ielts.isnot(None)).order_by(Program.ielts).all()
    ielts_scores = [str(score[0]) for score in ielts_scores if score[0]]  # Extract from tuple and convert to string

    # Get saved programs for current user
    saved_programs = [up.program_id for up in UserProgram.query.filter_by(user_id=current_user.id).all()]

    return render_template(
        "courses.html",
        courses=courses,
        universities=universities,
        fields=fields,
        locations=locations,
        ielts_scores=ielts_scores,
        total_pages=pagination.pages,
        page=page,
        has_prev=pagination.has_prev,
        has_next=pagination.has_next,
        prev_page=pagination.prev_num,
        next_page=pagination.next_num,
        saved_programs=saved_programs,
        username=current_user.username
        # degree_types and durations removed from context
    )

@app.route("/german_course_finder")
def german_course_finder():
    if "user" not in session:
        flash("Please login to access this page", "warning")
        return redirect(url_for("login"))
    return render_template("landing.html", username=session["user"])

@app.route("/universities")
@login_required
def universities():
    universities_list = University.query.all()
    saved_programs = get_saved_programs_for_user(current_user.id)  # if you use this
    return render_template(
        "universities.html",
        universities=universities_list,
        username=current_user.username,
        user=current_user,
        saved_programs=saved_programs,
        now=datetime.utcnow
    )
   
@app.route("/guest_login")
def guest_login():
    session["user"] = "guest"
    session["user_id"] = None
    session["role"] = "user"
    flash("Logged in as guest", "info")
    return redirect(url_for("landing"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        name = request.form.get("name", username)
        role = "user"  # Default to user

        # Only allow admin registration if current user is admin
        if session.get("role") == "admin":
            role = request.form.get("role", "user")

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return render_template("register.html")

        user = User(username=username, name=name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# Admin routes
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" not in session or session.get("role") != "admin":
        flash("Admin access required", "danger")
        return redirect(url_for("login"))
    universities = University.query.all()
    programs = Program.query.all()
    fields = FieldOfStudy.query.all()  # If you use fields in your add/edit forms
    return render_template(
        'admin_dashboard.html',
        universities=universities,
        programs=programs,
        fields=fields,
        universities_count=len(universities),
        programs_count=len(programs)
    )

@app.route("/admin/add_program", methods=["GET", "POST"])
def add_program():
    if "user" not in session or session.get("role") != "admin":
        flash("Admin access required", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        university_id = request.form["university_id"]
        field_of_study_id = request.form["field_of_study_id"]
        url = request.form.get("url", "")
        description = request.form.get("description", "")
        ielts = request.form.get("ielts", "")
        degree_type = request.form.get("degree_type", "")
        duration = request.form.get("duration", "")

        program = Program(
            name=name,
            university_id=university_id,
            field_of_study_id=field_of_study_id,
            url=url,
            description=description,
            ielts=ielts,
            degree_type=degree_type,
            duration=duration
        )
        db.session.add(program)
        db.session.commit()
        flash("Program added successfully!", "success")
        return redirect(url_for("courses"))

    universities = University.query.all()
    fields = FieldOfStudy.query.all()
    return render_template("add_program.html",
                         universities=universities,
                         fields=fields)

@app.route("/admin/manage_users")
def manage_users():
    if "user" not in session or session.get("role") != "admin":
        flash("Admin access required", "danger")
        return redirect(url_for("login"))

    users = User.query.all()
    return render_template("manage_users.html", users=users)

@app.route('/save_program/<int:program_id>', methods=['POST'])
@login_required
def save_program(program_id):
    existing = UserProgram.query.filter_by(user_id=current_user.id, program_id=program_id).first()
    if not existing:
        up = UserProgram(user_id=current_user.id, program_id=program_id)
        db.session.add(up)
        db.session.commit()
    flash("Program saved!", "success")
    return redirect(url_for('courses'))

@app.route('/remove_saved_program/<int:program_id>', methods=['POST'])
@login_required
def remove_saved_program(program_id):
    saved = UserProgram.query.filter_by(user_id=current_user.id, program_id=program_id).first()
    if saved:
        db.session.delete(saved)
        db.session.commit()
        flash('Course removed from saved items.', 'success')
    else:
        flash('Course not found in your saved items.', 'warning')
    return redirect(url_for('landing'))

@app.route("/logout")
def logout():
    username = session.get("user", "User")
    session.clear()
    flash(f"{username} has been logged out.", "info")
    return redirect(url_for("login"))

@app.route('/course/<int:program_id>')
@login_required
def course_detail(program_id):
    program = Program.query.get_or_404(program_id)
    return render_template('course_detail.html', program=program)

@app.route('/edit_university/<int:university_id>', methods=['POST'])
@login_required
def edit_university(university_id):
    uni = University.query.get_or_404(university_id)
    uni.name = request.form['name']
    uni.location = request.form['location']
    uni.website = request.form['website']
    db.session.commit()
    flash('University updated!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_university/<int:university_id>', methods=['POST'])
@login_required
def delete_university(university_id):
    uni = University.query.get_or_404(university_id)
    db.session.delete(uni)
    db.session.commit()
    flash('University deleted!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_program/<int:program_id>', methods=['POST'])
@login_required
def edit_program(program_id):
    prog = Program.query.get_or_404(program_id)
    prog.name = request.form['name']
    # Add other fields as needed
    db.session.commit()
    flash('Program updated!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_program/<int:program_id>', methods=['POST'])
@login_required
def delete_program(program_id):
    prog = Program.query.get_or_404(program_id)
    db.session.delete(prog)
    db.session.commit()
    flash('Program deleted!', 'success')
    return redirect(url_for('admin_dashboard'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    try:
        db.session.rollback()
    except Exception:
        pass
    return render_template('500.html'), 500

def add_test_data():
    with app.app_context():
        # First create some programs if none exist
        if Program.query.count() == 0:
            uni = University.query.first()
            field = FieldOfStudy.query.first()
            
            if uni and field:
                programs = [
                    Program(name="Computer Science Master", university_id=uni.id, 
                           field_of_study_id=field.id, ielts="6.5"),
                    Program(name="Engineering Bachelor", university_id=uni.id, 
                           field_of_study_id=field.id, ielts="6.0"),
                    # Add more sample programs as needed
                ]
                db.session.add_all(programs)
                db.session.commit()

if __name__ == "__main__":
    init_db()  # Initialize database and sample data
    app.run(debug=True, host='0.0.0.0', port=5000)
from app import db, Program
print(Program.query.all())
# WRONG! This is CSS, not Python:
# background: linear-gradient(120deg, #f0f4f8 0%, #e9ecef 100%);