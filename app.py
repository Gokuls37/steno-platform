"""
DT-STENO — Main Application
Start: gunicorn "app:create_app()"
"""
import os
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = os.environ.get('SECRET_KEY', 'dt-steno-dev-secret-2024')

    from auth.routes import auth_bp
    from student.routes import student_bp
    from admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(admin_bp,   url_prefix='/admin')

    @app.route('/')
    def index():
        from flask import render_template
        return render_template('landing.html')

    return app

# For gunicorn: gunicorn "app:create_app()"
app = create_app()

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)))
