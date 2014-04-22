
import oursql
import flask


_cached = {}


# db models
# Ideally, this class would be provided by a more established, production-ready framework like SQLAlchemy

class Model(object):
	m = None
	curs = None
	changed = []
	q = None

	def is_changed(self):
		return len(self.changed) > 0

	def __init__(self, *args, **kwargs):

		app = flask.current_app
		self.id = 0 

		d = []
		sql = ["SELECT * FROM %s " % self.table]
		for key in kwargs:
			if '__' in key:
				k = key.split("__")
				dkey = k[0]
				arg = k[1]
			else: 
				arg = False
				dkey = key

			if dkey in self.data:
				val = kwargs[key]

				if isinstance(val, long): val = int(val)

				if arg == "contains":			
					sql.append("%s LIKE ?" % dkey)
					d.append("%%%s%%" % val)
				else:
					sql.append("%s = ?" % dkey)
					d.append(val)

				# logic XXX

		if len(sql) > 1: sql[0] += "WHERE "	
		q = "%s%s" % (sql[0], ' AND '.join(sql[1:]))

		self.q = q
		self.d = d

		if q+str(d) in _cached: return 

		print q

                try:
                	self.curs=app.db.db.cursor(oursql.DictCursor)
	                self.curs.execute(q, d)
                except Exception as e:
			print str(e)
                        pass # XXX

	def __iter__(self):
		return self

	def next(self): # Python < 3.x

		self.id = self.id + 1
		self.m = None
		self.hydrate()
			
		if self.m is None and self.id > 1: raise StopIteration
		return self

	def __setitem__(self, key, val):

		self.hydrate()

		if key in self.m:
			if val == self.m[key]: return 
			self.m[key] = val
			self.changed.append(key)

	def __getitem__(self, key):
		self.hydrate()
	
		if self.m is not None and key in self.m: return self.m[key]
		else: return None

	def __delitem__(self, key):
		if self.m is None: self.new()
		if key in self.m: del self.m[key]

	def __str__(self):
		self.hydrate()
		return str(self.m)			

	def get(self):
		self.hydrate()
		return self.m

	def hydrate(self):
		if self.m is not None: return

		ckey = self.q + str(self.d)

		if ckey in _cached and self.id in _cached[ckey]: 
			self.m = _cached[ckey][self.id]
			return

		try:
			# No CACHE, but also no cursor...quickly execute cursor to fetch new row
			if self.curs is None:
				print "_cached execute: %s" % self.q	
				self.curs=app.db.db.cursor(oursql.DictCursor)
        	                self.curs.execute(self.q, self.d)

			self.m = self.curs.fetchone()

			if ckey in _cached: _cached[ckey][self.id] = dict(self.m)
			else: _cached[ckey] = {self.id: dict(self.m)}

			# XXX hydrate self.data 
		except:
			# The cursor probably has no rows remaining, so hydrate self with empty dict

			# Only set this to blank if we are not iterating
			if self.m is not None: self.new() 
			elif self.id == 1: self.id = 2 # hack to raise stopiteration from next() on first

		self.changed = []

	# filter XXX
	# set from dict

	def new(self):
		if self.curs: self.curs.close()
		self.m = self.data
		self.changed = []
		return self

	def set_dict(self, d):
		if self.m is None: self.new() # OK? XXX
		for key in d:
			if key in self.m: 
				self.m[key] = d[key]
				self.changed.append(key)
		return self

	def delete(self):
		self.hydrate()
		if self.m is None: return

		q = "DELETE FROM %s WHERE ID = ?" % self.table
	
		print "%s (%d)" % (q, self['ID'])

		try:
			c=flask.current_app.db.db.cursor(oursql.DictCursor)
                        c.execute(q, [self['ID']])
		except Exception as e:
			flask.flash(str(e))
			
		return 

	def invalidate_cache(self):
		global _cached
		_cached = {} # XXX big hammer

	def insert(self):
		d = {}
		sql = ["INSERT INTO %s " % self.table]
		row = dict(self.m) # need one(self) XXX	
		for k in row:
			if row[k] is None or len(str(row[k])) <= 0: continue
                        if isinstance(row[k], long): d[k] = int(row[k]) # OurSQL and python long dont work well together
			else: d[k] = row[k]
			sql.append("?")	
		
		q = sql[0] + "(" + ','.join(d.keys()) + ")"
		q += " VALUES (" + ','.join(sql[1:]) + ")"

		print "%s (%s)" % (q, str(d))

		ret = False
		try:
			c=flask.current_app.db.db.cursor(oursql.DictCursor)
			c.execute(q, d.values())
			ret = c.lastrowid
			c.close()
		except Exception as e:
			flask.flash("%s Insert Failed: %s" % (self.table, str(e)) )
			print str(e)
			pass

		# hydrate with self.primary/curs.lastrowid
		return ret		

	def update(self):

		dk = []
		dv = []
		primary = "ID" if not hasattr(self, 'primary') else self.primary
		sql = ["UPDATE %s SET " % self.table]
		self.hydrate()
		row = dict(self.m) # XXX
		for k in row:
			if k == primary or row[k] is None: continue
			if k not in self.changed: continue
			dk.append(k)
			dv.append(row[k])

		if len(dk) <= 0: return 

		q = sql[0] + '=?,'.join(dk) + "=?"
		q += " WHERE " + primary + "=?"
		dv.append(self.m[primary])

		print "%s (%s)" % (q, str(dv))

		try:
			c=flask.current_app.db.db.cursor(oursql.DictCursor)
			c.execute(q, dv)
			c.close()
			ret=True
			self.changed=[]
		except Exception as e:
                        flask.flash("%s Update Failed: %s" % (self.table, str(e)) )
			print str(e)
			ret=False

		return ret


class user(Model):
	data = {"ID":'', "Username":"", "Password":"", "date_created":"", "date_modified":"", "status":"", "Company":""}
	table = "Users"

	def __init__(self, user_id=None, email=None, **kwargs):
		if user_id is not None:
			super(user, self).__init__(ID=user_id, status=1)
		elif email is not None:
			super(user, self).__init__(email=email, status=1)
		else:
			super(user, self).__init__(kwargs)

	def get_customers(self):
		return customer(owner_id=self['ID'])

	def get_services(self):
		return service(owner_id=self['ID'])

	def get_quotes(self):
		return quotes(owner_id=self['ID'])

	def get_appointments(self):
		return appointments(user_id=self['ID'])

	def get_access(self):
		return access(user_id=self['ID'])


class customer_contact(Model):
	data = {'ID':'', 'customer_id':'', 'contact_type':'', 'name':'', 'data':'', 'created_by':'', 'date_created':'', 'date_modified':''}
	table = "Customers_Contact"

	def get_customer(self):
		return customer(ID=self['customer_id'])
	

class customers(Model):
	data = {'ID':'', 'Name':'', 'customer_type':'', 'primary_contact_id':'', 'owner_id':'', 'date_created':'', 'date_modified':'', 'status':''}
	table = "Customers"

	def get_contacts(self):
		return customer_contact(customer_id=self['ID'])

	def get_primary_contact(self):
		return customer_contact(ID=self['primary_contact_id'])

	def get_owner(self):
		return user(user_id=self['owner_id'])

	def get_services(self):
		return services(customer_id=self['ID'])


class services(Model):
	table = "Services"
	data = {'ID':'','customer_id':'','Name':'','service_type':'','description':'','owner_id':'','date_created':'','date_modified':'','status':''}

	def get_customer(self):
		return customers(ID=self['customer_id'])

	def get_owner(self):
		return user(ID=self['owner_id'])

	def get_quotes(self):
		return quotes(service_id=self['ID'])
	
	def get_appointments(self):
		return appointments(service_id=self['ID'])


class quotes(Model):
	table = "Quotes"
	data = {'ID':'','service_id':'','quote_type':'','amount':'','paid':'','owner_id':'','date_created':'','date_modified':'','status':''}

	def get_service(self):
		return services(ID=self['service_id'])

	def get_owner(self):
		return user(ID=self['owner_id'])


class appointments(Model):
	table = "Appointments"
	data = {'ID':'','service_id':'','user_id':'','scheduled':'','actual':'','extra':'','date_created':'','date_modified':'','status':''}

	def get_service(self):
		return services(ID=self['service_id'])

	def get_user(self):
		return user(ID=self['user_id'])


class access(Model):
	table = "Access"
	data = {'ID':'','user_id':'','date_created':'','date_modified':'','created_by':'','access_type':'','access_rule':'','access_data':''}

	def get_user(self):
		return user(ID=self['user_id'])


