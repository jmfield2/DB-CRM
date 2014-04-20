
from flask import render_template, request, session
from flask import redirect, flash
from functools import update_wrapper

import oursql

import datetime

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


	# Customers 

	# customers.init_views(app)

	@app.route("/customers/search.json")
	@auth_required()
	def customer_search_json():
		# sEcho, iTotalRecords, iTotalDisplayRecords

		# sSearch?
		if request.args.get("sSearch", False) is not False:
			c = customers(Name__contains=request.args.get("sSearch"))
		else: 
			c = customers()

		from flask import url_for

		data = []
		for row in c:
			owner = row.get_owner()['Username'] if row.get_owner() is not None else "N/A "
			links = "<a href='%s'>Edit</a> | <a href='%s'>Delete</a>" % (url_for('customer_edit', id=int(row['ID'])), url_for('customer_delete', id=int(row['ID'])))
			data.append([row['customer_type'], row['Name'], owner, str(row['date_created']), row['status'], links])

		resp = {'aaData':data}

		import json
		return json.dumps(resp)

	# delete
	@app.route("/customers/delete/<int:id>")
	@auth_required()
	def customer_delete(id):
		return ""

	# delete_confirm

	# edit
	@app.route("/customers/edit/<int:id>", methods=['GET', 'POST'])
	@auth_required()
	def customer_edit(id):
		u = user(user_id=session['uid']).get()

                return render_template("customer_edit.html", user=u)

        @app.route("/customers/add", methods=['GET', 'POST'])
	@auth_required()
        def customer_add():
                u = user(user_id=session['uid']).get()
                del u['Password']

		if 'customer_type' in request.form:
			d = {"status":1, "owner_id":u['ID'], "customer_type":request.form.get('customer_type', False), "Name":request.form.get('Name', False), "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}

			id = customers().set_dict(d).insert()
	
			# customers_contact customer_id contact_type name data 
			if id is not False:
				cid = False
				names = ["email", "phone", "address-street", "address-city", "address-state"]
				
				for name in names:
					if request.form.get(name, False) is not False and len(request.form.get(name)) > 0:
						d = {"contact_type":request.form.get('contact_type', 'main'), "customer_id":id,'name':name,'data':request.form.get(name, False), "created_by":session['uid'], "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}

						ret = customer_contact().set_dict(d).insert()			
						if cid == False: cid = ret

				# XXX ENFORCE UNIQUE ON CUSTOMERS_CONTACT XXX

				# dynamic details
				names = request.form.getlist("contact-name[]")
				values = request.form.getlist("contact-data[]")
				for i in range(0, len(names)):
					name = names[i]
					val = values[i]

					d = {"contact_type":request.form.get('contact_type', 'main'), "customer_id":id,'name':name,'data':val, "created_by":session['uid'], "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}

                                        ret = customer_contact().set_dict(d).insert()
                                        if cid == False: cid = ret					

				if cid is not False:
					c = customers(ID=id)
					c['primary_contact_id'] = cid
					c.update()

				flash("Customer Added (ID=%d)" % id)

			# services customer_id Name service_type description owner_id status
			if id is not False and request.form.get('service-type', False) is not False:
				d = {"customer_id":id, "Name":request.form.get("service-name"), "description":request.form.get("service-description"), "service_type":request.form.get("service-type"), "owner_id":session['uid'], "status":1, "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}
				if d["service_type"] == "Other": d["service_type"] = request.form.get("service-other-type", "")					
				s = services().set_dict(d).insert()
	
				# quotes service_id, quote_type amount owner_id status
				d = {"service_id":s, "quote_type":request.form.get("quote-type"), "amount":request.form.get("quote-amount"), "owner_id":session['uid'], "status":1, "paid":0, "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}
				quotes().set_dict(d).insert()

				# appointments service_id user_id scheduled extra status
				d = {"service_id":s, "user_id":request.form.get('contact-quote-user'), "scheduled":request.form.get("appointment-date"), "extra":"-", "status":1, "actual":"0000-00-00", "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}

				appointments().set_dict(d).insert()

				flash("Service Added (ID=%d)" % s)

                return render_template("customer_add.html", user=u)

        @app.route("/customers/index")
	@auth_required()
        def customer_index():
		u = user(user_id=session['uid']).get()
		del u['Password']

                return render_template("customer_index.html", user=u)


	# Users

        @app.route("/userprofile.html")
	@auth_required()
        def userprofile():
                return render_template("userprofile.html")

	# Access

