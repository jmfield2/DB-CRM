
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

	@app.route("/help")
	def help():
		return render_template("help.html")

	# the remaining views below require authentication

	@app.route("/dashboard")
	@app.route("/")
	@auth_required()
	def dashboard():
		u = user(user_id=session['uid']).get()
		if 'Password' in u: del u['Password']

		db = appointments(user_id=u['ID'])
		a = []
		import copy
		for row in db: a.append(copy.copy(row))
		a = sorted(a, key=lambda x: x['scheduled'])

		return render_template("index.html", user=u, appt=a)


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
		u = user(user_id=session['uid']).get()
		c = customers(ID=id).get()

		return render_template("customer_delete.html", user=u, customer=c)

	# delete_confirm
	@app.route("/customers/delete_confirm/<int:id>")
	@auth_required()
	def customer_delete_confirm(id):
	
		c = customers(ID=id)

		import copy
		l = []
		for row in c.get_contacts(): l.append(copy.copy(row))
		for row in c.get_services(): 
			l.append(copy.copy(row))
			for row2 in row.get_quotes(): l.append(copy.copy(row2))
			for row2 in row.get_appointments(): l.append(copy.copy(row2))

		for row in l: row.delete()

		c.delete()

		c.invalidate_cache()
	
		flash("Customer deleted")

		return redirect( flask.url_for("customer_index") )

	# edit
	@app.route("/customers/edit/<int:id>", methods=['GET', 'POST'])
	@auth_required()
	def customer_edit(id):
		u = user(user_id=session['uid']).get()

		c = customers(ID=id)

		if len(request.form) > 0:

			# edit customer
                        d = {"customer_type":request.form.get('customer_type', c['customer_type']), "Name":request.form.get('Name', c['Name'])}
			c.set_dict(d)
			if c.is_changed(): 	
				d["date_modified"] = datetime.datetime.now()
				c.set_dict(d)
				c.update()

			# edit customer_contacts
			import copy
			type = request.form.get('contact_type', False)

			if c.get_primary_contact().get() is not None:
				ct = customer_contact(customer_id=c['ID'], contact_type=c.get_primary_contact()["contact_type"])
				for row in ct:
					tmp = copy.copy(row)
					tmp["name"] = request.form.get("contact-name-" + str(row["ID"]), tmp["name"])
					tmp["data"] = request.form.get("contact-" + str(row["ID"]), tmp["data"])
					tmp["contact_type"] = type
					if tmp.is_changed(): 
						tmp["date_modified"] = datetime.datetime.now()
						tmp.update()
						flash("Customer updated")

                        names = request.form.getlist("contact-name-new")
                        values = request.form.getlist("contact-new")

			for i in range(0, len(names)):
				if len(names[i]) <= 0 or len(values[i]) <= 0: continue

				ct = customer_contact().new()
				ct["customer_id"] = c["ID"]
				ct["created_by"] = session['uid']
				ct["contact_type"] = type
				ct["name"] = names[i]
				ct["data"] = values[i]
				ct["date_created"] = datetime.datetime.now()
				ct["date_modified"] = datetime.datetime.now()

				retid = ct.insert()

				if retid is not False and c.get_primary_contact().get() is None:
					c['primary_contact_id'] = retid
					c.update()

			# edit services
			for row in c.get_services():
				tmp = copy.copy(row)
				tmp["status"] = request.form.get("service-%d-status" % tmp["ID"], tmp["status"])
				tmp["service_type"] = request.form.get("service-%d-service_type" % tmp["ID"], tmp["service_type"])
				tmp["Name"] = request.form.get("service-%d-Name" % tmp["ID"], tmp["Name"])
				tmp["description"] = request.form.get("service-%d-description" % tmp["ID"], tmp["description"])
				if tmp.is_changed():
			 		tmp["date_modified"] = datetime.datetime.now()
					tmp.update()
					flash("Service updated")

				# edit quotes
				for s in row.get_quotes():
					tmp = copy.copy(s)
					tmp["quote_type"] = request.form.get("quote-%d-type" % tmp["ID"], tmp["quote_type"])
					tmp["amount"] = request.form.get("quote-%d-amount" % tmp["ID"], tmp["amount"])
					tmp["paid"] = request.form.get("quote-%d-paid" % tmp["ID"], tmp["paid"])
					tmp["status"] = request.form.get("quote-%d-status" % tmp["ID"], tmp["status"])
					tmp["owner_id"] = request.form.get("quote-%d-owner_id" % tmp["ID"], tmp["owner_id"])
					if tmp.is_changed():
						tmp["date_modified"] = datetime.datetime.now()
						tmp.update()
						flash("Quote updated")

				# edit appointments
				for s in row.get_appointments():
					tmp = copy.copy(s)
					tmp['user_id'] = request.form.get("appt-%d-user_id" % tmp["ID"], tmp["user_id"])
					tmp["scheduled"] = request.form.get("appt-%d-scheduled" % tmp["ID"], tmp["scheduled"])
					tmp["actual"] = request.form.get("appt-%d-actual" % tmp["ID"], tmp["actual"])
					tmp["extra"] = request.form.get("appt-%d-extra" % tmp["ID"], tmp["extra"])
					tmp["status"] = request.form.get("appt-%d-status" % tmp["ID"], tmp["status"])
					if tmp.is_changed():
						tmp["date_modified"] = datetime.datetime.now()
						tmp.update()
						flash("Appointment updated")

				# new quotes
				s = request.form.get("quote-new-%d-status" % row["ID"], False)
				if s is not False and len(s) > 0: 
					tmp = quotes().new()
					tmp["service_id"] = row["ID"]
					tmp["owner_id"] = request.form.get("quote-new-%d-owner_id" % row["ID"], False)
					tmp["quote_type"] = request.form.get("quote-new-%d-type" % row["ID"], False)
					tmp["amount"] = request.form.get("quote-new-%d-amount" % row["ID"], False)
					tmp["paid"] = request.form.get("quote-new-%d-paid" % row["ID"], False)
					tmp["status"] = request.form.get("quote-new-%d-status" % row["ID"], False)
					tmp["date_created"] = datetime.datetime.now()
					tmp["date_modified"] = datetime.datetime.now()
					tmp.insert()

					flash("Quote added")

				# new appointments
				s = request.form.get("appt-new-%d-status" % row["ID"], False)
				if s is not False and len(s) > 0:
					tmp = appointments().new()
					tmp["service_id"] = row["ID"]
					tmp["user_id"] = request.form.get("appt-new-%d-user_id" % row["ID"], False)
					tmp["status"] = request.form.get("appt-new-%d-status" % row["ID"], False)
					tmp["extra"] = request.form.get("appt-new-%d-extra" % row["ID"], False)
					tmp["actual"] = request.form.get("appt-new-%d-actual" % row["ID"], False)
					tmp["scheduled"] = request.form.get("appt-new-%d-scheduled" % row["ID"], False)
					tmp["date_created"] = datetime.datetime.now()
					tmp["date_modified"] = datetime.datetime.now()
					tmp.insert()
					flash("Appointment added")
	
			# new service
                        # services customer_id Name service_type description owner_id status
                        if id is not False and request.form.get('service-type', False) is not False:
                                d = {"customer_id":c["ID"], "Name":request.form.get("service-name"), "description":request.form.get("service-description"), "service_type":request.form.get("service-type"), "owner_id":session['uid'], "status":1, "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}
                                if d["service_type"] == "Other": d["service_type"] = request.form.get("service-other-type", "")
                                s = services().set_dict(d).insert()

                                # quotes service_id, quote_type amount owner_id status
                                d = {"service_id":s, "quote_type":request.form.get("quote-type"), "amount":request.form.get("quote-amount"), "owner_id":session['uid'], "status":1, "paid":0, "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}
                                quotes().set_dict(d).insert()

                                # appointments service_id user_id scheduled extra status
                                d = {"service_id":s, "user_id":request.form.get('contact-quote-user'), "scheduled":request.form.get("appointment-date"), "extra":"-", "status":1, "actual":"0000-00-00", "date_created":datetime.datetime.now(), "date_modified":datetime.datetime.now()}
                                appointments().set_dict(d).insert()

                                flash("Service Added (ID=%d)" % s)

			# reload
			c.invalidate_cache()
			c = customers(ID=id) 

			flash( "Customer Updated. (%s) " % request.form )

                return render_template("customer_edit.html", user=u, c=c, customer=c.get(), customer_contact=customer_contact)

        @app.route("/customers/add", methods=['GET', 'POST'])
	@auth_required()
        def customer_add():
                u = user(user_id=session['uid']).get()
                if 'Password' in u: del u['Password']

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
		if 'Password' in u: del u['Password']

                return render_template("customer_index.html", user=u)


	@app.route("/services/delete/<int:id>")
	@auth_required()
	def services_delete(id):
		next = request.referrer

		s = services(ID=id)
		s.delete()
		flash("Service Deleted")
		
		s.invalidate_cache()

		return redirect(next)

	# Users

        @app.route("/user/profile", methods=['GET','POST'])
	@auth_required()
        def user_profile():
		u = user(user_id=session['uid']).get()
		if 'Password' in u: del u['Password']

                return render_template("user_profile.html", user=u)

	@app.route("/users/search.json")
	@auth_required()
	def user_search_json():
		q = request.args.get("q", False)

		resp = []
		if q is not False:
			u = user(Name__contains=q)
			for row in u:
				resp.append({'value': row["ID"], "user":row['Username']})

		import json
		return json.dumps(resp)

	@app.route("/users/settings")
	@auth_required()
	def user_settings():
		u = user(user_id=session['uid']).get()
                if 'Password' in u: del u['Password']
		
		return render_template("user_settings.html", user=u)

	# Access

