#
# Views
#
from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    """Return the main view."""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = try_login_user(email, password)
        if user is None:
            error = u'Login failed'
            flash(error)
        else:
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    logout_user()
    flash(u'You were logged out')
    return redirect(url_for('index'))


@app.route('/parent_portal/',  methods=['GET', 'POST'])
def portal():
    pass


#
# APIs
#   
@app.route('api/parent/<parent>', methods=['GET', 'POST', 'DELETE', 'UPDATE'])
def parent(parent):
    pass
    
    
@app.route('api/student/<student>', methods=['GET', 'POST', 'DELETE', 'UPDATE'])
def student(student):
    pass
    
@app.route('api/location/<location>', methods=['GET', 'POST', 'DELETE', 'UPDATE'])
def location(location):
    pass
    
@app.route('api/location/<location>/class/<class>', methods=['GET', 'POST', 'DELETE', 'UPDATE'])
def class(location, class):
    pass
    
    
#
# Error Handling
#

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500