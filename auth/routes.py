import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify

auth_bp = Blueprint('auth', __name__)
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        from database.db import authenticate_student
        data = request.get_json() or request.form
        mobile   = str(data.get('identifier', data.get('mobile',''))).strip().replace(' ','').replace('-','')
        password = str(data.get('password','')).strip()
        student, err = authenticate_student(mobile, password)
        if student:
            session.clear()
            session['student_id']   = student['StudentID']
            session['student_name'] = student.get('Name','Student')
            session['role']         = 'student'
            if request.is_json: return jsonify({'status':'ok','redirect': url_for('student.dashboard')})
            return redirect(url_for('student.dashboard'))
        if request.is_json: return jsonify({'status':'error','message': err or 'Login failed'}), 401
        return render_template('login.html', error=err)
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        from database.db import register_student, get_class_code, get_student_by_mobile
        data     = request.get_json() or request.form
        name     = str(data.get('name','')).strip()
        mobile   = str(data.get('mobile','')).strip().replace(' ','').replace('-','')
        password = str(data.get('password','')).strip()
        code     = str(data.get('class_code','')).strip().upper()
        if not all([name, mobile, password, code]):
            msg = 'All fields are required.'
            if request.is_json: return jsonify({'status':'error','message':msg}), 400
            return render_template('register.html', error=msg)
        if len(mobile) < 10 or not mobile.isdigit():
            msg = 'Enter a valid 10-digit mobile number.'
            if request.is_json: return jsonify({'status':'error','message':msg}), 400
            return render_template('register.html', error=msg)
        if len(password) < 6:
            msg = 'Password must be at least 6 characters.'
            if request.is_json: return jsonify({'status':'error','message':msg}), 400
            return render_template('register.html', error=msg)
        if code != get_class_code().upper():
            msg = 'Invalid class code. Contact your instructor.'
            if request.is_json: return jsonify({'status':'error','message':msg}), 400
            return render_template('register.html', error=msg)
        if get_student_by_mobile(mobile):
            msg = 'This mobile number is already registered.'
            if request.is_json: return jsonify({'status':'error','message':msg}), 400
            return render_template('register.html', error=msg)
        sid = register_student(name, mobile, password, code)
        if request.is_json:
            return jsonify({'status':'ok','student_id':sid,'message':'Registration submitted! Wait for instructor approval.'})
        return render_template('register.html', success='Submitted! Your instructor will approve your account.')
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        data = request.get_json() or request.form
        pw   = str(data.get('password','')).strip()
        if pw == ADMIN_PASSWORD:
            session.clear()
            session['role'] = 'admin'
            if request.is_json: return jsonify({'status':'ok','redirect': url_for('admin.dashboard')})
            return redirect(url_for('admin.dashboard'))
        msg = 'Incorrect password.'
        if request.is_json: return jsonify({'status':'error','message':msg}), 401
        return render_template('admin/login.html', error=msg)
    return render_template('admin/login.html')

@auth_bp.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('auth.admin_login'))
