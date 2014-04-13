
from flask import render_template, request, session
from flask import redirect, flash
from functools import update_wrapper

import oursql


# check login
def auth_required():
        def decorator(f):
                def wrapped(*args, **kwargs):
			if 'uid' in session: 
				uid = session['uid']

				# check for ACL rules in Access table for URL and UID

	                        return f(*args, **kwargs)
			else: return redirect("/login?next=%s" % request.url, code=302) # query_string 

                return update_wrapper(wrapped, f)
        return decorator


def configure_views(app):

	# db models
	class user:
		m = None

		def __init__(self, user_id=None, email=None):
			if user_id is not None:
			        sql = "SELECT * FROM Users where ID = ? AND status = 1"
				data = [user_id]
			elif email is not None:
				sql = "SELECT * FROM Users where Username = ? AND status = 1"
				data = [email]
		
	                curs=app.db.db.cursor(oursql.DictCursor)
        	        try:
        		        curs.execute(sql, data)
                        	self.m = curs.fetchone()
			except:
				pass

		def get(self):
			return self.m

		# get, set

	# Access, Appointments, Customers/Customer_Contact, Quotes, Services

	@app.route("/logout")
	def logout():
		if 'uid' in session: del session['uid']

		return redirect("/login")

        @app.route("/login.html", methods=['GET', 'POST'])
	@app.route("/login", methods=['GET', 'POST'])
        def login():
		next = request.args.get('next', '/dashboard') 

		from urlparse import urlparse
		o = urlparse(next)
		next = o[2] # Only allow relative PATH -- dont arbitrarily redirect to user-submitted URL

		# passlib algorithm as crypt for seamless namespace (pbkdf2_sha512, bcrypt)
		from passlib.hash import pbkdf2_sha512 as crypt

		if 'email' in request.form:
			sql = "SELECT * FROM Users where Username = ? AND status = 1"
        	        curs=app.db.db.cursor(oursql.DictCursor)
			try:
		                curs.execute(sql, [request.form['email']])
                		user = curs.fetchone()
				if user is not None and crypt.verify(request.form['password'], user['Password']):
					session['uid'] = user['ID']
					return redirect(next)
				else: flash("Invalid user/password")
			except Exception as e:
				print str(e)
				flash("An unexpected error occurred")
			curs.close()
		
                return render_template("login.html", url=request.url)



	# the remaining views below require authentication

	@app.route("/dashboard")
	@app.route("/")
	@auth_required()
	def dashboard():
		u = user(session['uid']).get()

		del u['Password']
		return render_template("index.html", user=u)

		
	# Services, Quotes, Appointments
	# Finish appointment ...

        @app.route("/addcustomer.html")
	@auth_required()
        def customer_add():
                return render_template("addcustomer.html")

        @app.route("/customer.html")
	@auth_required()
        def customer():
                return render_template("customer.html")

        @app.route("/userprofile.html")
	@auth_required()
        def userprofile():
                return render_template("userprofile.html")

	
