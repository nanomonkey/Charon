from flaskapp import db, User

db.create_all() 

login = User('email', 'password')

for item in [login]:
	db.session.add(item)

db.session.commit()