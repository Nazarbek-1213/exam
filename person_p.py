import json
import os
class Student:
    def __init__(self,fullname,age,grade,major):
        self.fullname=fullname
        self.age=age
        self.grade=grade
        self.major=major
    def show(self):
        return f"fullname:{self.fullname},age:{self.age},grade:{self.age},major:{self.major}"

def add_std():
    fullname = input("fullname: ")
    age = int(input("age: "))
    grade = input("grade: ")
    major = input("major: ")
    student1 = Student(fullname, age, grade, major)
    student1_dict = student1.__dict__
    try:
        with open('students.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    data.append(student1_dict)
    with open('students.json', 'w') as f:
        json.dump(data, f, indent=4)

def view_all_student():
    try:
     with open('students.json', 'r') as f:
         data = json.load(f)
    except FileNotFoundError:
        data = []
    return data
def update_info():
    view_all_student()
    a=input("name: ")
add_std()