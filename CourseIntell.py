import sqlite3
import itertools
import math
import numpy as np
import numpy.polynomial.polynomial as poly
import matplotlib.pyplot as plt

# connect to the database
conn = sqlite3.connect('data.db')
c = conn.cursor()


# Calculate Percentage
def percentage(scores, low, high, total):
    counts = 0.0
    for s in scores:
        if low <= s <= high:
            counts = counts + 1
    percent = counts/total*100
    return np.around(percent, decimals=0)


# Subject Analysis
def subject_analysis(score_list):
    score_list.sort()
    print "Highest Marks : ", score_list[len(score_list)-1]
    pass_percentage = percentage(score_list, 40, 100, len(score_list))
    fail_percentage = 100 - pass_percentage
    print "Pass Percentage : " + str(pass_percentage) + " %"
    print "Fail Percentage : " + str(fail_percentage) + " %"
    print "Percentage of Students in 40-50% Slab : " + str(percentage(score_list, 40, 50, len(score_list))) + " %"
    print "Percentage of Students in 51-60% Slab : " + str(percentage(score_list, 51, 60, len(score_list))) + " %"
    print "Percentage of Students in 61-70% Slab : " + str(percentage(score_list, 61, 70, len(score_list))) + " %"
    print "Percentage of Students in 71-80% Slab : " + str(percentage(score_list, 71, 80, len(score_list))) + " %"
    print "Percentage of Students in 81-90% Slab : " + str(percentage(score_list, 81, 90, len(score_list))) + " %"
    print "Percentage of Students in 91-100% Slab : " + str(percentage(score_list, 91, 100, len(score_list))) + " %"


# Marks in the main subject
def main_subject_marks(college_id, main_subject):
    q = "SELECT " + main_subject + " FROM marks WHERE id = '" + college_id + "'"
    c.execute(q)
    main_subject_score = c.fetchall()
    return main_subject_score[0]


# Function to return marks of students in prerequisites
def prerequisites_marks(college_id, base):
    q = base + " FROM marks WHERE id = '" + college_id + "'"
    c.execute(q)
    return c.fetchall()


# Function to return marks data of a particular student
def marks_of_student(college_id, base):
    q = base + " FROM marks WHERE id = '" + college_id + "'"
    c.execute(q)
    return c.fetchall()


# Function to calculate correlation
def correlation(x, y):
    mean_x = 0
    mean_y = 0
    sigma_xy = 0
    sigma_x_squares = 0
    sigma_y_squares = 0
    xx = list()
    yy = list()

    for i, j in itertools.izip(x, y):
        mean_x += i
        mean_y += int(j)

    mean_x /= len(x) * 1.0
    mean_y /= len(y) * 1.0

    for i, j in itertools.izip(x, y):
        xx.append(i - mean_x)
        yy.append(int(j) - mean_y)

    for a, b in itertools.izip(xx, yy):
        sigma_xy += a * b
        sigma_x_squares += a * a
        sigma_y_squares += b * b

    r = sigma_xy / (math.sqrt(sigma_x_squares * sigma_y_squares))
    return np.around(r, decimals=3)


# Taking student id and subject as input
print "\n"
print "-----------------------------------------------------"
print "IntellCourse - An Intelligent Course Selection System "
print "-----------------------------------------------------"
print"\n"
print "Input"
print "-----------------------------------------------------"
student_id = raw_input('Enter College ID : ')
subject = raw_input('Enter Subject To Estimate Marks : ')
marks_list = list()
print "\n"


# Get the subject prerequisites and its weights
query = "SELECT * FROM weights WHERE subject = '" + subject + "'"
c.execute(query)
row = c.fetchall()
if len(row) == 0:
    print "Invalid Input"
    exit(0)
col_names = [k[0] for k in c.description]
prerequisites = list()
weights = {}
for k, d in itertools.izip(col_names, row[0]):
    if k == 'SUBJECT' or d == '0' or k == subject:
        continue
    prerequisites.append(k)
    weights[k] = d


# Get the list of subjects taken by the student
# Get the marks in the subjects
query = "SELECT * FROM marks WHERE id = '" + student_id + "'"
c.execute(query)
rows = c.fetchall()
if len(rows) == 0:
    print "Invalid Input"
    exit(0)
col_name = [k[0] for k in c.description]
subjects = list()
marks = list()
for k, d in itertools.izip(col_name, rows[0]):
    if k == 'ID' or d == 0 or k == subject:
        continue
    subjects.append(k)
    marks.append(int(d))


# Check if the student has taken the prerequisites, if not then exit
for k in prerequisites:
    if k not in subjects:
        print "Prerequisites not taken"
        exit(0)


# Get other student ids who have taken the subject whose marks for the main student has to be estimated
query = "SELECT id, " + subject + " from marks"
c.execute(query)
data = c.fetchall()
if len(data) == 0:
    print "Insufficient Data"
    exit(0)
college_ids = list()
for row in data:
    if row[1] != 0:
        marks_list.append(int(row[1]))
        college_ids.append(row[0])
if not college_ids:
    print "Insufficient Data"
    exit(0)


# Form base query to get data for all students in common subjects with the main student
base_query = "SELECT " + subjects[0]
count = 1
for k in subjects:
    if count == 1:
        count = 0
        continue
    base_query += "," + k


# Get the student ids whose similarity index is greater than 0.5 with the main student
# Correlation method is used
correlation_id = list()
for k in college_ids:
    if str(k) == student_id:
        continue
    data = marks_of_student(str(k), base_query)
    co = correlation(marks, data[0])
    if co > 0.5:
        correlation_id.append(k)
if not correlation_id:
    print "Insufficient Data"
    exit(0)


# Base query to get marks of students in prerequisite subjects
base_query = "SELECT " + prerequisites[0]
count = 1
for k in prerequisites:
    if count == 1:
        count = 0
        continue
    base_query += "," + k


# Calculate the aggregate of each student based on prerequisite (i.e x value in linear regression)
# Also get the y value from the marks table
x_values = list()
y_values = list()
for k in correlation_id:
    data = prerequisites_marks(str(k), base_query)
    aggregate = 0.0
    for p, rw in itertools.izip(prerequisites, data[0]):
        aggregate = aggregate + (float(weights[p]) * float(rw))
    x_values.append(aggregate)
    y_values.append((int(main_subject_marks(k, subject)[0])))


# Get the x and y value for the main student
data = prerequisites_marks(student_id, base_query)
aggregate = 0.0
for p, rw in itertools.izip(prerequisites, data[0]):
    aggregate = aggregate + (float(weights[p]) * float(rw))
x_main_student = aggregate
y_main_student = int(main_subject_marks(student_id, subject)[0])


# Linear Regression y = a + bx
coefficients = poly.polyfit(x_values, y_values, 1)
calculated_y = coefficients[0] + x_main_student*coefficients[1]
calculated_y = int(np.around(calculated_y, decimals=0))


# Output Results
print "Results"
print "-----------------------------------------------------"
print "Actual Marks : ", y_main_student
print "Estimated Marks : ", calculated_y
print "\n"


# Output Subject Analysis
print "Subject Analysis"
print "-----------------------------------------------------"
subject_analysis(marks_list)
print "\n"


# Plotting Linear Regression
plt.scatter(x_values, y_values, color='b')
plt.plot(x_values, poly.polyval(x_values, coefficients), color='r', linewidth=3)
plt.xlabel("Aggregate marks of prerequisites using weights")
plt.ylabel("Marks of "+subject)
plt.title("Linear Regression to Estimate Subject Marks")
plt.show()


# Close database connection
c.close()
conn.close()
