# EduHire Course Finder Flask Application

## **Overview**

This application is a web-based Course Finder built using Flask and SQLAlchemy. It allows users to browse, search, and save university programs, with separate dashboards and features for users and admins. The app includes user authentication, role-based access, and persistent data storage via SQLite.

---

## **Key Features**

### 1. **User Authentication & Authorization**
- Users can register, login, and logout.
- Passwords are hashed using Werkzeug for security.
- Role-based access: **admin** and **user**.
- Admins have access to dashboards for managing universities, programs, and users.
- Guest login allows quick, non-persistent access for demo/testing.

### 2. **Database Models**

| Model         | Fields                                                                                                                                                | Relationships                                |
|---------------|------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------|
| User          | id, username, password_hash, name, role, created_at                                                                                                  | saved_programs (UserProgram)                 |
| University    | id, name, location, website                                                                                                                          | programs (Program)                           |
| FieldOfStudy  | id, name                                                                                                                                             | programs (Program)                           |
| Program       | id, name, university_id, field_of_study_id, url, description, ielts, degree_type, duration                                                           | university (University), field_of_study (FieldOfStudy), user_programs (UserProgram) |
| UserProgram   | id, user_id, program_id                                                                                                                              | user (User), program (Program)               |

- **UserMixin** from Flask-Login is used for session management.

### 3. **App Structure & Routing**

- **Home:** Redirects to login.
- **Login:** Handles user authentication with database and fallback dummy users.
- **Register:** User registration. Only admins can create admin accounts.
- **Landing:** User dashboard displaying saved programs.
- **Courses:** Search and filter university programs by university, location, field, IELTS requirements, etc., with pagination.
- **University Management:** Admins can add, edit, and delete universities.
- **Program Management:** Admins can add, edit, and delete programs.
- **User Management:** Admins can view all registered users.
- **Save/Remove Programs:** Users can save or remove programs to/from their profile.

### 4. **Filtering & Search**

- Full-text search on program names, descriptions, and university names.
- Filter by university, location, field, and IELTS score (including "No IELTS Required").
- Paginated results for course listings.

### 5. **Admin Panel**

- Centralized dashboard for managing universities, programs, and users.
- Quick stats on the number of universities and programs.
- Admin privileges required for dashboard and management routes.

### 6. **Error Handling**

- Custom error pages for 404 and 500 errors.
- Database session rollback on server errors.

### 7. **Sample Data & Initialization**

- On first run, creates admin user and sample universities, fields, and programs if tables are empty.
- Includes functions for adding test/demo data.

---

## **Code Quality & Best Practices**

- **Security:** Uses password hashing, login protection, and session keys.
- **Separation of Concerns:** Models, routes, and templates are logically organized.
- **Extensibility:** Easy to add new fields, filters, or user roles.
- **Database Initialization:** Handles first-time setup and sample data population.
- **Error Management:** Handles common web errors gracefully.

---

## **Deployment & Running**

- Uses SQLite for local development (easy to swap for PostgreSQL/MySQL).
- App runs with `debug=True`, but this should be set to `False` for production.
- The secret key should be set from an environment variable in production.

**To run:**
```bash
python app.py
# or the appropriate entrypoint if using a different filename
```

---

## **Possible Improvements**

- **Template Structure:** Extract repeated code into macros/includes for DRYness.
- **API Endpoints:** Add RESTful endpoints for AJAX or external integration.
- **Tests:** Add unit and integration tests for models and routes.
- **User Profiles:** Allow users to update their details/passwords.
- **Role Management:** Allow for more granular roles/permissions.
- **Admin Audit Logs:** Track admin actions for accountability.
- **Better Error Messages:** Provide more context and recovery options to users.

---

## **Conclusion**

This Course Finder application is a robust foundation for a university/program discovery platform. It demonstrates best practices in Flask application design, secure user authentication, and clean code organization. With some enhancements, it could be production-ready for broader deployment or further feature expansion.
