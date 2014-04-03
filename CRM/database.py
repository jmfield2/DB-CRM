# -*- coding:utf-8 -*-

#--- SQLALCHEMY SUPPORT

#def drop_all():
#    db.drop_all()


#def create_all():
#    db.create_all()


#def remove_session():
#    db.session.remove()

#--- SQLALCHEMY SUPPORT END

import oursql

class dbClass:
	def init_app(self, app):
		self.db = oursql.connect(passwd=app.config["DB_PASS"], db=app.config["DB_NAME"], host=app.config["DB_HOST"], user=app.config["DB_USER"])

		@app.teardown_appcontext
		def db_close(error):
			self.db.close()

db = dbClass()


