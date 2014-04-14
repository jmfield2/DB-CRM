
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


from models import *

def configure_views(app):

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
		u = user(user_id=session['uid']).get()
		del u['Password']

		return render_template("index.html", user=u)

	# XXX make these blueprints?

	# Customers 

	@app.route("/customers/search.json")
	@auth_required()
	def customer_search_json():
		# sEcho, iTotalRecords, iTotalDisplayRecords
		resp = {'aaData':[['type','name','user','date','status','actions']]}

		import json
		return json.dumps(resp)

	# delete

        @app.route("/customers/add")
	@auth_required()
        def customer_add():
                return render_template("customer_add.html")

        @app.route("/customers/index")
	@auth_required()
        def customer_index():
		u = user(user_id=session['uid']).get()
		del u['Password']

                return render_template("customer_index.html", user=u)


	# Services

	# Quotes

	# Appointments/Tasks

	# Users

        @app.route("/userprofile.html")
	@auth_required()
        def userprofile():
                return render_template("userprofile.html")

	# Access

