from charon import db, User, Parent, Student, Classroom
from datetime import date

db.create_all() 

login = User('scott@altschool.com', 'password')
parent1 = Parent('Scott', 'Garrison', '3203 Market St.', 'Oakland', '94608', login, '(805)231-8709')
student1 = Student('lil_Scott', 'Scott', gender=MALE, dob=date(1,1,1), state=ACTIVE) 
class1 = Classroom(name='2015 Folsom K1', description="", tuition=19100.00, capacity=24, start_date=date(1,1,1), end_date=date(1,2,1), status=0)

for item in [login, parent1, student1, class1]:
	db.session.add(item)

student1.add_parent(parent1)
student1.add_to_class(class1, date(2014, 1, 1), date(2014, 12, 31))

db.session.commit()