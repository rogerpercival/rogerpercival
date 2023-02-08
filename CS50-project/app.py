# cs50 project
# v1.15
# 8th Feb 2023
# Roger S Percival

# Import python functions
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import cs50
import csv
import pandas as pd
import sqlite3 as sql
from sqlite3 import Error
import glob

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

dbname = "static/cs50-project.db"
tablename = ""
csvdata = []

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = cs50.SQL("sqlite:///"+dbname)

MAX_NEW_FIELDS = 9


@app.route('/')
def home():
	return render_template('index.html')


# --------------- CREATE CONNECTION ------------------
# Create a connection to database 'dbname' and return SQL connection object 'conn' (or none)
def create_connection(level, dbname):

    conn = None
    try:
    	conn = sql.connect(dbname)
    	return conn
    except Error as e:
    	flash(e)
    	layout = getLayout(level)
    	return render_template(layout)

# --------------- GET LAYOUT -----------------

def getLayout(level):

	try:
		if level == 1:
			layout = "layout-2.html"
		if level == 2:
			layout = "layout-3.html"
		if level == 3:
			layout = "layout-4.html"
		return layout
	except Exception as e:
		flash(e)
		return

# --------------- GET LEVEL ------------------
def getLevel():

	SQLStr = 'SELECT level FROM Users where idx = ' + str(session['user_id'])
	db = cs50.SQL("sqlite:///"+dbname)
	row = db.execute(SQLStr)
	level = int(row[0]['level'])
	return level


# --------------- GET USER NAME ------------------
def getUserName():

	db = cs50.SQL("sqlite:///"+dbname)
	SQLQuery = 'SELECT username FROM Users WHERE idx = '+ str(session["user_id"])
	rows = db.execute(SQLQuery)
	username = rows[0]["username"]
	return username


# --------------- GET COLUMN NAMES FROM DATATABLE --
# obtained from pandas dataframe using df.columns

def getColumnNames(level, tablename):

	columnNames = []
	try:
		df = createDF_from_table(level, tablename)
		columnNames = list(df.columns)
		return columnNames

	except Exception as e:
		flash(e)
		return


# --------------- GET COLUMN TYPES -------------------
# obtained from SQL table using SQL query
def getColumnTypes(level, tablename):

	try:
		columnTypes = []
		conn = create_connection(level, dbname)
		fieldresults = conn.execute("PRAGMA table_info('%s')" % tablename).fetchall()
		for i in range(len(fieldresults)):
			columnTypes.append(fieldresults[i][2])
		return columnTypes
	except Exception as e:
		flash(e)
	return


# --------------- CREATE SQL COLUMN STRING -----------
def createSQLColumnStr(level, columnNames):

	SQLColumnStr = '('
	try:
		for i in range(1,len(columnNames)-1):
			SQLColumnStr = SQLColumnStr + columnNames[i] +', '
		SQLColumnStr = SQLColumnStr + columnNames[i+1] + ') '
		return (SQLColumnStr)

	except Exception as e:
		flash(e)
	return


# --------------- CREATE SQL VALUES STRING -----------
def createSQLValueStr(columnNames, columnTypes, columnValues):

	SQLValueStr = '('
	try:
		for i in range(len(columnValues)-1):
			if columnTypes[i+1] == 'TEXT':
				tmpStr = "'" + columnValues[i] + "', "
				SQLValueStr = SQLValueStr + tmpStr
			else:
				if columnValues[i].isnumeric() == True:
					SQLValueStr = SQLValueStr + columnValues[i] +', '
				else:
					flash(f"You have not entered an integer for Column '{columnNames[i]}'")
					return
		if columnTypes[i+1] == 'TEXT':
				tmpStr = "'" + columnValues[i+1] + "'"
				SQLValueStr = SQLValueStr + tmpStr +')'
		else:
			if columnValues[i+1].isnumeric() == True:
				SQLValueStr = SQLValueStr + columnValues[i+1] +')'
			else:
				flash(f"You have not entered an integer for Column '{columnNames[i+2]}'")
				return
		return (SQLValueStr)

	except Exception as e:
		flash(e)
	return

# --------------- CREATE SQL UPDATE STRING -----------
def createSQLUpdateStr(columnTypes, columnNames, columnValues):

	try:
		SQLUpdateStr = ''
		for i in range(len(columnValues)-1):
			if columnTypes[i+1] == 'TEXT':
				SQLUpdateStr = SQLUpdateStr + columnNames[i+1] + " = '" + columnValues[i] + "', "
			if columnTypes[i+1] == 'INTEGER':
				SQLUpdateStr = SQLUpdateStr + columnNames[i+1] + " = " + columnValues[i] +', '

		if columnTypes[i+2] == 'TEXT':
			SQLUpdateStr = SQLUpdateStr + columnNames[i+2] + " = '" + columnValues[i+1] + "'"
		if columnTypes[i+2] == 'INTEGER':
			SQLUpdateStr = SQLUpdateStr + columnNames[i+2] + ' = ' + columnValues[i+1]

		return SQLUpdateStr
	except Exception as e:
		flash(e)
		return

# --------------- CREATE PANDAS DATAFRAME FROM SQL DATABASE --------
# requires table name as input
def createDF_from_table(level, tablename):

	layout = getLayout(level)
	conn = create_connection(level, dbname)
	SQLQuery='SELECT * FROM ' + tablename
	try:
		SQLQuery = pd.read_sql_query (SQLQuery, conn)
		df = pd.DataFrame(SQLQuery)
		fields = df.columns
		num_fields = df.shape[1] - 1
		return df
	except Exception as e:
		flash(e)
		return render_template(layout)
	return render_template(layout)


# --------------- CREATE PANDAS DATAFRAME FROM SQL DATABASE FIELDS--------
# requires table name as input to retrieve fields

def createDF_from_table_fields(level, tablename):

	layout = getLayout(level)
	conn = create_connection(level, dbname)
	SQLQuery='SELECT name FROM PRAGMA_table_info("' + tablename + '")'

	try:
		SQLQuery = pd.read_sql_query (SQLQuery, conn)
		df = pd.DataFrame(SQLQuery)
		fields = df.columns
		num_fields = df.shape[1] - 1
		return df
	except Exception as e:
		flash(e)
		return render_template(layout)
	return render_template(layout)



# --------------- CREATE PANDAS DATAFRAME FROM CSV FILE --------
# requires CSV file name as input
def createDF_from_csv(csvfilename):

	try:
		df = pd.read_csv(csvfilename, na_values = ['.', 'no info'])
		csvfilename =csvfilename.replace('static/csv/', '')
		return df

	except Exception as e:
		flash(e)
		return render_template('layout-4.html')
	return render_template('layout-4.html')


# --------------- GET COLUMN TYPES FOR PANDAS WRITE ----------

def createDFTypes(df, tablename):

	level = getLevel()
	try:
		dtypedict = {}
		columnTypes = getColumnTypes(level, tablename)
		columnNames = getColumnNames(level, tablename)
		for i in range(len(columnNames)):

			if columnTypes[i] == 'INTEGER':
				dtypedict.update({columnNames[i] : 'INTEGER'})
			if columnTypes[i] == 'REAL':
				dtypedict.update({columnNames[i] : 'REAL'})
			if columnTypes[i] == 'TEXT':
				dtypedict.update({columnNames[i] : 'TEXT'})
		return dtypedict

	except Exception as e:
		flash(e)
	return

# --------------- WRITE PANDAS DATAFRAME TO SQL TABLE --------
# requires dataframe and table name as input for existing table
def writeDF_to_SQL(level, df: pd.DataFrame, tablename):

	if tablename != 'Users':
		layout = getLayout(level)
	conn = create_connection(level, dbname)

	try:
		#use panda module to save dataframe in sqlite table
		dtypedict = createDFTypes(df, tablename)

		df.to_sql(tablename, conn, dtype=dtypedict, index_label = "idx", if_exists="replace")
		conn.commit()
		return df

	except Exception as e:
		flash(e)
		return render_template(layout)
	return render_template(layout)

# --------------- WRITE PANDAS DATAFRAME TO SQL TABLE --------
# requires dataframe and table name as input for imported table
def writeDF_to_SQL2(level, df: pd.DataFrame, tablename):

	if tablename != 'Users':
		layout = getLayout(level)
	conn = create_connection(level, dbname)

	try:
		#use panda module to save dataframe in sqlite table
		df.to_sql(tablename, conn, index_label = "idx", if_exists="replace")
		conn.commit()
		return df
	except Exception as e:
		flash(e)
		return render_template(layout)
	return render_template(layout)


# --------------- WRITE PANDAS DATAFRAME TO SQL TABLE --------
# requires dataframe and table name as input
def writeDFReg_to_SQL(level, df: pd.DataFrame, tablename):

	conn = create_connection(level, dbname)

	try:
		#use panda module to save dataframe in sqlite table
		dtypedict = createDFTypes(df, tablename)

		df.to_sql(tablename, conn, dtype=dtypedict, index_label = "idx", if_exists="replace")
		conn.commit()

		return df
	except Exception as e:
		flash(e)
		return render_template("login.html")
	return render_template("login.html")

# --------------- GENERATE TABLE FOR DISPLAY --------
# requires dataframe and table name as input
def generate_table(level, tablename):

	layout = getLayout(level)
	try:
		df = createDF_from_table(level, tablename)

		# generate table.html for this table (changes for each table)
		process_dataframe(df, tablename)

		# Construct SQL query string and generate  record for selected table
		SQLStr = 'SELECT * FROM ' + tablename
		# Get data for selected table
		records = db.execute(SQLStr)
		return records
	except Exception as e:
		flash(e)
		return render_template(layout)

@app.route('/showstudents')
def showstudents():

	level = getLevel()
	username = getUserName()
	layout = getLayout(level)

	try:
		# Create dataframe to get number of columns and column names
		tablename = 'Students'

		df = createDF_from_table(level, tablename)

		# Drop idx field so it is not shown in table displayed
		if level == 1:
			index_column='idx'
			df = df.drop(index_column, axis=1)

		fields = df.columns
		num_fields = df.shape[1] - 1
		process_dataframe(df, tablename)
		#db = cs50.SQL("sqlite:///cs50-project.db")
		records = db.execute("select * from Students")

		if level == 1:
			return render_template("table-0.html",username=username, records=records, dbname=dbname, tablename=tablename, fields=fields, num_fields=num_fields)
		if (level == 2) or (level == 3):
			return render_template("table.html",username=username, records=records, dbname=dbname, tablename=tablename, fields=fields, num_fields=num_fields)

	except Exception as e:
		flash(e)
		return render_template(layout, username=username)


# --------------- SHOW COURSE TABLE  ------------------
# Display database table Courses
@app.route('/showcourses')
def showcourses():

	level = getLevel()
	username = getUserName()
	layout = getLayout(level)

	try:
		# Create dataframe to get number of columns and column names
		tablename = 'Courses'
		df = createDF_from_table(level, tablename)
		# Drop idx field so it is not shown in table displayed
		if level == 1:
			index_column='idx'
			df = df.drop(index_column, axis=1)


		fields = df.columns
		num_fields = df.shape[1] - 1
		process_dataframe(df, tablename)


		#db = cs50.SQL("sqlite:///cs50-project.db")
		records = db.execute("SELECT * from Courses")

		if level == 1:
			return render_template("table-0.html",username=username, records=records, dbname=dbname, tablename=tablename, fields=fields, num_fields=num_fields)
		if (level == 2) or (level == 3):
			return render_template("table.html",username=username, records=records, dbname=dbname, tablename=tablename, fields=fields, num_fields=num_fields)

	except Exception as e:
		flash(e)
		return render_template(layout,username=username)


# --------------- PROCESS DATA FRAME ------------------
# TBD - get field names and work out how to get eacb row
def process_dataframe(dataframe: pd.DataFrame, tablename):
	num_fields = len(list(dataframe))
	field_names = list(dataframe)

	level=getLevel()
	layout = getLayout(level)

	extendsStr1 = '{% extends "layout-1.html" %}'
	extendsStr1 = '{% extends "' + layout + '" %}'

	#if level == 1:
	#	extendsStr1 = '{% extends "layout-2.html" %}'
	#if level == 2:
	#	extendsStr1 = '{% extends "layout-3.html" %}'
	#if level == 3:
	#	extendsStr1 = '{% extends "layout-4.html" %}'

	extendsStr1a = '{% block title %} <title>' + tablename + '</title>{% endblock %}   {% block content %}'

	extendsStr = extendsStr1 + extendsStr1a

	table_html1 = f"""
							<div class="container">
      					<div class="row">
        					<div class="col-sm-4">
   					"""
	table_html1a = '<h4>Database : {{ dbname }}</h4></div><div class="col-sm-4"><h4>Table : {{ tablename }}</h4></div>'
	table_html1b = f"""
      					</div>
     					 	<div class="row">
							<div class="col-sm-12">
							<form name="add" action="/getfields" method="post">
							<input name="table" hidden value="{ tablename }">
							<button class="add-button" type="submit" title="add"><span>Add record</span></button>
							</form>

							<table id="mytable" class="table table-striped table-bordered table-condensed nowrap" style="width: 100%">
							<thead style="background-color: #0271c9; color: white;">
                  	<tr>
 							"""

	table_html1 = extendsStr + table_html1 + table_html1a + table_html1b

	table_html2 = '<th class="action-width"></th><th class="action-width"></th>'
	for field in range(1,num_fields):
		table_html2 = table_html2 + '<th>' + field_names[field] + '</th>'

	theadstr = '</thead><tbody>'
	table_html2 = table_html2 + theadstr
	loopstr = '{% for record in records %}'
	table_html3 = f"""
                		<tr>
                		<td>
                 		<form  name="delete" action="/deleterecord" method="post">
  							<input name="table" type="hidden"
   					"""
	table_html3a 		= 'placeholder={{ tablename }} value={{ tablename }}>'

	table_html3b = '<input name="idx" hidden value=" {{ record.' + field_names[0] + ' }}"><button class="delete-button" type="submit" title="delete"><span>Delete</span></button></form></td>'

	table_html3c = f"""
                		<td>
                 		<form name="edit" action="/getfields3" method="post">
  							<input name="table" type="hidden"
   					"""
	table_html3d 		= 'placeholder={{ tablename }} value={{ tablename }}>'

	table_html3e = '<input name="idx" hidden value=" {{ record.' + field_names[0] + ' }}"><button class="edit-button" type="submit" title="edit"><span>Edit</span></button></form></td>'

	table_html3 = loopstr + table_html3 + table_html3a + table_html3b + table_html3c + table_html3d + table_html3e

	table_html4 = ""
	for field in range(1,num_fields):
		table_html4 = table_html4 + '<td> {{ record.' + field_names[field] + ' }} </td>'
		# table_html4 = table_html4 + '<td> {{ record.' + str(field) + ' }} </td>'

	table_html5 = f"""
							</tr>
   					"""

	endforstr = '{% endfor %}'

	table_endstr = f"""
                		</tbody>
        					</table>
							</div>
							</div>
							</div>
						"""

	endstr = '{% endblock %}'

	table_html5 = table_html5 + endforstr + table_endstr + endstr

	html = table_html1 + table_html2 + table_html3 + table_html4 + table_html5

	open("templates/table.html", "w").write(html)

	return



# --------------- DELETE RECORD ------------------
@app.route('/deleterecord', methods=['GET', 'POST'])
def deleterecord():

	idx = request.form.get("idx")
	tablename = request.form.get("table")
	username = getUserName()
	level = getLevel()
	layout = getLayout(level)

	if request.method == 'GET':
		return redirect("/listtables")

	try:
		if (tablename == 'Users' and int(idx) == 0):
			flash("You can't delete the 'admin' user")
			return redirect("/deleterecord")

		# Construct SQL query string and delete record for selected table
		SQLStr = 'DELETE FROM ' + tablename + ' WHERE idx = ' + str(idx)
		db = cs50.SQL("sqlite:///" + dbname)
		result = db.execute(SQLStr)

		records = generate_table(level, tablename)

		flash(f'Record {str(idx)} deleted successfully')
		return render_template("table.html", username=username, records=records, tablename=tablename, dbname=dbname)

	except Exception as e:
		flash(f'Delete record failed - {e}')
		return render_template(layout,username=username)


# --------------- DELETE FIELD ------------------
@app.route('/deletefield', methods=['POST'])
def deletefield():
	columnname = request.form.get("columnname")
	tablename = request.form.get("table")
	level = getLevel()
	layout = getLayout(level)
	username = getUserName()

	try:

		conn=create_connection(level, dbname)
		df = createDF_from_table(level,tablename)

		if tablename == 'Users':
			flash("You can't delete any Column in the Users table")
			return redirect('/listfields')

		index_column='idx'
		df = df.drop([index_column, columnname], axis=1)

		writeDF_to_SQL(level, df, tablename)

		# Construct SQL query string with returned table name
		SQLStr = 'SELECT * FROM ' + tablename

		flash(f'Column "{columnname}" deleted successfully')

	except Exception as e:
		flash(e)
		return render_template(layout, username=username, dbname=dbname, tablename=tablename)
	return redirect('/listfields')



# --------------- GET FIELDS (for add record )  ------------------
@app.route('/getfields' , methods=['GET', 'POST'])
def getfields():

	tablename = request.form['table']
	username = getUserName()
	level = getLevel()
	layout = getLayout(level)

	if tablename == 'Users':
		flash("You can't add a new user. Use 'REGISTER'")
		return redirect("/listtables")

	if request.method == 'POST':
		try:
			conn=create_connection(level, dbname)

			# get the fields in selected table but remove idx (will be added back in when new record is added)
			results = conn.execute("PRAGMA table_info('%s')" % tablename).fetchall()

			results.pop(0)
			return render_template("addrecord.html", username=username, results=results, dbname=dbname, tablename=tablename)

		except Exception as e:
			flash(f'Column retrieval failed - {e}')
			return render_template(layout, username=username, dbname=dbname, tablename=tablename)

	return render_template("addrecord.html",username=username, tablename=tablename)

# --------------- ADD FIELD ------------------
@app.route('/addfield',methods = ['GET', 'POST'])
def addfield():

	tablename = request.form.get("table")
	fieldname = request.form.get("fieldname")
	fieldtype = request.form.get("fieldtype")

	level=getLevel()
	username = getUserName()

	if request.method == 'POST':
		try:
			if ' ' in fieldname :
				fieldname = fieldname.replace(' ', '_')
			if '-' in fieldname:
				fieldname = fieldname.replace('-', '_')
			df = createDF_from_table(level, tablename)

			# Remove 'idx' column since it will be recreated when datatable written to database
			df=df.drop(df.columns[0], axis=1)

			# Add new column to datatable with data according to fieldtypes
			if fieldtype == 'TEXT':
				df.loc[:,fieldname] = 'NaN'
			if fieldtype == 'INTEGER':
				df.loc[:,fieldname] = 0
			if fieldtype == 'REAL':
				df.loc[:,fieldname] = 0.0

			# Write new datatable (with new column) to database (idx field added automatically)
			writeDF_to_SQL(level, df, tablename)

			flash(f'New column "{fieldname}" added to table "{tablename}"')

		except Exception as e:
			flash(f'{e} (is table empty ?)')
		return redirect("listfields")
	return redirect("listfields")


# --------------- GET FIELDS (for edit record )  ------------------
@app.route('/getfields3' , methods=['GET', 'POST'])
def getfields3():

	username = getUserName()
	level = getLevel()

	tablename = request.form['table']
	idx = request.form.get("idx")
	conn=create_connection(level, dbname)

	# get the fields in selected table but remove idx (will be added back in when new record is added)
	res = conn.execute("PRAGMA table_info('%s')" % tablename).fetchall()
	results = [list(i) for i in res]

	# Get all columns for selected user
	SQLQuery = 'SELECT * from ' + tablename + ' WHERE idx = ' + str(idx)
	data  = conn.execute(SQLQuery).fetchall()

	# Add the values to the results list after column name field (which currently only has column names)
	for i in range(len(results)):
		results[i].insert(2,data[0][i])
	results.pop(0)

	return render_template("editrecord.html", username=username, idx=idx, results=results, dbname=dbname, tablename=tablename)


# --------------- EDIT RECORD ------------------
@app.route('/editrecord',methods = ['GET', 'POST'])
def editrecord():

	username = getUserName()
	level = getLevel()
	layout = getLayout(level)

	if request.method == 'GET':
		return render_template(layout, username=username)

	if request.method == 'POST':

		columnValues = []
		SQLQuery = ''

		try:
			tablename = request.form.get("table")
			idx = request.form.get("idx")

			columnTypes = getColumnTypes(level, tablename)
			columnNames = getColumnNames(level, tablename)
			if tablename != 'Users':
				for i in range(1,len(columnNames)):
					columnValues.append(request.form.get(columnNames[i]))

			# Special case if Users table is being editted, retain username and password hash
			# Only allow 'level' to be modified
			if tablename == 'Users':
				SQLQuery = 'SELECT username, hash from ' + tablename + ' WHERE idx = ' + str(idx)
				results = db.execute(SQLQuery)
				columnValues.append(results[0]['username'])
				columnValues.append(results[0]['hash'])
				columnValues.append(request.form.get("level"))

			# Create strings for columns and values portions for SQL query
			#SQLColumnStr = createSQLColumnStr(level, columnNames)
			#SQLValueStr = createSQLValueStr(columnNames, columnTypes, columnValues)
			SQLUpdateStr = createSQLUpdateStr(columnTypes, columnNames, columnValues)

			# Constuct SQL Query and execute it
			SQLQuery = 'UPDATE '+ tablename + ' SET ' + SQLUpdateStr + ' WHERE "idx" = ' + str(idx)
			db.execute(SQLQuery)

			# This is to remove index column from database and rewrite with a new index column
			# needed since adding a record cannot add unique index value
			df = createDF_from_table(level, tablename)

			df=df.drop(df.columns[0], axis=1)

			writeDF_to_SQL(level, df, tablename)

			# Get table to display it
			SQLQuery = 'SELECT * from ' + tablename
			records = db.execute(SQLQuery)

			flash('Record editted successfully')
			return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)

		except Exception as e:
			flash(e)
			return render_template(layout, username=username)


# --------------- ADD RECORD ------------------
@app.route('/addrecord',methods = ['GET', 'POST'])
def addrecord():

	username = getUserName()
	level = getLevel()
	layout = getLayout(level)
	i = 0

	if request.method == 'GET':
		return render_template(layout, username=username)

	if request.method == 'POST':

		columnValues = []
		SQLQuery = ''

		try:

			tablename = request.form.get("table")

			columnTypes = getColumnTypes(level, tablename)
			columnNames = getColumnNames(level, tablename)

			for i in range(1,len(columnNames)):
				columnValues.append(request.form.get(columnNames[i]))

			# Create strings for columns and values portions for SQL query
			SQLColumnStr = createSQLColumnStr(level, columnNames)
			SQLValueStr = createSQLValueStr(columnNames, columnTypes, columnValues)

			# Construct SQL Query and execute it
			SQLQuery = 'INSERT INTO '+ tablename + SQLColumnStr + ' VALUES' + SQLValueStr
			db.execute(SQLQuery)

			# This is to remove index column from database and rewrite with a new index column
			# needed since adding a record cannot add unique index value
			df = createDF_from_table(level, tablename)
			df=df.drop(df.columns[0], axis=1)
			writeDF_to_SQL(level, df, tablename)

			# Get table to display it
			SQLQuery = 'SELECT * from ' + tablename
			records = db.execute(SQLQuery)

			flash('Record added successfully')
			return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)

		except Exception as e:
			flash(e)
			return render_template(layout, username=username)


# --------------- GET FIELDS (for add field )  ------------------
@app.route('/getfields2' , methods=['GET', 'POST'])
def getfields2():

	username = getUserName()
	level = getLevel()
	layout = getLayout(level)
	fieldtypes = ['TEXT', 'INTEGER', 'REAL']

	if request.method == 'GET':

		tablename = request.form.get("table")
		return render_template("addcolumn.html", tablename=tablename, username=username)

	if request.method == 'POST':

		fields = []

		try:
			tablename = request.form.get("table")
			SQLQuery = 'SELECT count (*) FROM ' + tablename
			conn = create_connection(level, dbname)
			count = conn.execute(SQLQuery).fetchone()
			count = int(count[0])
			if count == 0:
				flash("You can't add a column to an empty table")
				return redirect("/listfields")
			df = createDF_from_table(level, tablename)

		except Exception as e:
			flash(e)

		return render_template("addcolumn.html", fieldtypes=fieldtypes, tablename=tablename, username=username)



# --------------- LIST TABLES ------------------
@app.route('/listtables', methods = ['POST', 'GET'])
def listtables():

	level = getLevel()
	layout = getLayout(level)
	username = getUserName()

	# Set up connection to Database
	conn = create_connection(level, dbname)

	if request.method == 'GET':

		# Get list of tables to populate dropdown list
		tablenames = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
		# Set tablename to first table in list
		tablename='None selected'

		if level == 2:
			return render_template("table-list-1.html", username=username, tablename=tablename, tablenames=tablenames, dbname=dbname)
		if level == 3:
			return render_template("table-list-2.html", username=username, tablename=tablename, tablenames=tablenames, dbname=dbname)

	if request.method == 'POST':
		if not request.form.get("table"):
			flash("Please select a table")
			return redirect("/listtables")

		try:
			# Get selected table name
			tablename = request.form['table']

			SQLQuery = 'SELECT * FROM ' + tablename
			df = pd.read_sql_query(SQLQuery, conn)

			# generate table.html for this table
			process_dataframe(df, tablename)

			# Get data for selected table
			db = cs50.SQL("sqlite:///"+dbname)
			records = db.execute(SQLQuery)

			return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)

		except Exception as e:
			flash(f'Show table failed - {e}')
			return render_template(layout, username=username)



# --------------- LIST FIELDS ------------------
@app.route('/listfields', methods = ['POST', 'GET'])
def listfields():

	level = getLevel()
	layout = getLayout(level)
	username = getUserName()

	# Set up connection to Database
	conn = create_connection(level, dbname)

	if request.method == 'GET':

		# Get list of tables to populate dropdown list
		try:
			tablenames = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

			tablename = 'None selected'
		except Exception as e:
			flash(e)
		return render_template("column-list-1.html", username=username, tablename=tablename, tablenames=tablenames, dbname=dbname)


	if request.method == 'POST':
		if not request.form.get("table"):
			flash("Please select a table")
			return redirect("/listfields")
		try:
			tablename = request.form["table"]


			# Get list of tables to populate dropdown list
			tablenames = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

			# Get data for selected table
			# Get field names (column_names) for selected table
			column_names = conn.execute("PRAGMA table_info('%s')" % tablename).fetchall()
			column_names.pop(0)
		except Exception as e:
			flash(e)
		tablename = request.form["table"]
		username = getUserName()
		return render_template("column-list-2.html",username=username, tablename=tablename, tablenames=tablenames, dbname=dbname, column_names=column_names)


# --------------- CREATE TABLE ------------------
@app.route("/createtable", methods = ['POST', 'GET'])
def createtable():

	level = getLevel()
	#layout = getLayout(level)
	username = getUserName()

	if request.method == 'GET':
		#flash("Create a new table")
		return render_template("create-table-1.html", username=username, dbname=dbname)

	if request.method == 'POST':

		if not request.form.get("tablename"):
			flash("You need to enter a table name")
			return render_template("create-table-1.html")
		if not request.form.get("fields"):
			flash("You need to enter the number of fields")
			return render_template("create-table-1.html")

		tablename = request.form["tablename"]

		if '-' in tablename:
			tablename = tablename.replace('-', '_')
			flash ('"-" not allowed, changed to "_"')

		if ' ' in tablename:
			tablename = tablename.replace(' ', '_')
			flash ('"spaces" not allowed, changed to "_"')

		fields = request.form["fields"]

		if not fields.isnumeric():
			flash ('You must enter a number')
			return render_template("create-table-1.html", username=username)

		if int(fields) < 1 or int(fields) > MAX_NEW_FIELDS :
			flash(f"You must enter a number between 1 and {MAX_NEW_FIELDS}")
			return render_template("create-table-1.html", username=username)

		field = int(request.form["fields"])

		#records = generate_table(level, tablename)

		#return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)
		return render_template("create-table-2.html", username=username, dbname=dbname, tablename=tablename, field=field)

		# return render_template("create-table-1.html")


# --------------- MAKE TABLE ------------------
@app.route("/maketable", methods = ['POST', 'GET'])
def maketable():

	level = getLevel()
	layout = getLayout(level)
	username = getUserName()

	fld = []
	fieldStr = ""

	if request.method == 'GET':

		return render_template("create-table-2.html", username=username, tablename=tablename, dbname=dbname)

	if request.method == 'POST':

		try:
			tablename = request.form.get("tablename")
			field = int(request.form.get("field"))

			SQLQuery = 'CREATE TABLE IF NOT EXISTS ' + tablename + " ('idx' integer, "
			for i in range(field):
				fname = request.form.get("field" + str(i))
				fieldStr = fieldStr + "'" + fname + "' text, "

			SQLQuery = SQLQuery + fieldStr +')'
			SQLQuery = SQLQuery.replace(', )', ')')

			records = db.execute(SQLQuery)
			flash(f'Table "{tablename}" created with "{field}" fields')

			# Create table does not create unique index so need to -
			# Create dataframe from database, remove index column and rewrite dataframe to database
			df = createDF_from_table(level,tablename)
			df = df.drop(df.columns[0], axis=1)
			writeDF_to_SQL(level, df, tablename)

			records = generate_table(level, tablename)
			return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)

		except Exception as e:
			flash(e)
			return redirect("/createtable")


# --------------- DELETE TABLE ------------------
@app.route("/deletetable", methods=["GET", "POST"])
def deletetable():

	level = getLevel()
	layout = getLayout(level)
	username = getUserName()

	# list tables if using GET
	if request.method == 'GET':

		# Get a list of all tables in the DB
		conn = create_connection(level, dbname)
		tablenames = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
		return render_template("delete-table.html", tablenames=tablenames, dbname=dbname, username=username)

	# delete table if using POST
	if request.method == 'POST':
		try:
			if not request.form.get("tabletodelete"):
				flash("Please select a table")
				return redirect("/deletetable")

			tablename = request.form["tabletodelete"]

			if tablename == 'Users':
				flash("You can't delete the 'Users' table")
				return redirect("/deletetable")

			conn = create_connection(level, dbname)
			# create string to use with SQL execute
			SQLStr = "DROP TABLE if exists " + tablename
			result = conn.execute(SQLStr)

			# display the list of tables following the drop
			tablenames = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
			flash(f'Table "{tablename}" successfully deleted')
			return render_template(layout,username=username)

		except Exception as e:
			flash(f'Delete table failed - {e}')
			return render_template(layout,username=username)

# --------------- CLEAR TABLE ------------------
# decide on page to return to
@app.route("/cleartable", methods=["GET", "POST"])
def cleartable():

	level = getLevel()
	layout = getLayout(level)
	username = getUserName()

	# list tables if using GET
	if request.method == 'GET':
		# Get a list of all tables in the DB

		conn = create_connection(level, dbname)
		tablename = 'None selected'
		tablenames = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
		return render_template("clear-table.html", username=username, tablenames=tablenames, dbname=dbname)

	# clear table data if using POST
	if request.method == 'POST':
		if not request.form.get("tabletoclear"):
			flash("Please select a table")
			return redirect("/cleartable")

		try:
			tablename = request.form["tabletoclear"]
			if tablename == 'Users':
				flash("You can't clear the 'Users' table")
				return redirect("/cleartable")

			conn = create_connection(level, dbname)

			# create string to use with SQL execute
			SQLStr = "DELETE FROM " + tablename
			result = conn.execute(SQLStr)
			conn.commit()
			flash(f'Table "{tablename}" data deleted')

			# display the list of tables following the drop
			tablenames = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

			records = generate_table(level, tablename)
			return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)

		except Exception as e:
			flash(f'Delete table data failed - {e}')
			return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)
		#return render_template("clear-table.html", username=username, tablenames=tablenames, dbname=dbname)


# ---------- IMPORT CSV -----------
@app.route('/importCSV', methods = ['GET', 'POST'])
def importCSV():

	level = getLevel()
	layout = getLayout(level)
	username = getUserName()
	csvfiles = glob.glob("static/csv/*.csv")

	if request.method == 'GET':

		for i in range(len(csvfiles)):
			csvfiles[i] = csvfiles[i].replace('static/csv/', '')
		return render_template("getcsvfile.html", username=username, csvfiles=csvfiles, dbname=dbname)

	if request.method == 'POST':
		if not request.form.get("csv"):
			flash("Please specify CSV filename")

		if not request.form.get("table"):
			flash("Please specify Table name")

		csvfilename = 'static/csv/' + request.form["csv"]
		tablename = request.form["table"]

		try:
			df = createDF_from_csv(csvfilename)

			# Replace spaces in column names with underscore
			df.columns = df.columns.str.replace(' ', '_')
			df.columns = df.columns.str.replace('-', '_')

			# Limit number of records for testing
			#df = df.iloc[:200]

			# Write dataframe to SQL table
			writeDF_to_SQL2(level, df, tablename)

			# This is needed since field 'idx' was only created on writing DF to SQL table
			#df = createDF_from_table(level, tablename)

			# Generate table.html for this table
			# process_dataframe(df, tablename)

			records = generate_table(level, tablename)

			# Get data for selected table
			#db = cs50.SQL("sqlite:///"+dbname)
			SQLQuery = 'SELECT * FROM ' + tablename

			records = db.execute(SQLQuery)

			msg = str(len(df)) + ' records, ' + str(df.shape[1] - 1) + ' fields imported into table "' + tablename + '" successfully'
			flash(msg)

			return render_template("table.html", username=username, records=records, dbname=dbname, tablename=tablename)

		except Exception as e:
			flash(e)
			return render_template(layout, username=username, dbname=dbname)
	return render_template(layout, username=username, dbname=dbname)


# --------------- LOG OUT ------------------
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    flash('You have been logged out')
    # Redirect user to login form

    return render_template("login.html")


# --------------- LOG IN ------------------
@app.route("/login", methods=["GET", "POST"])
def login():

	"""Log user in"""

	# Forget any user_id
	session.clear()

	if request.method == "GET":
		return render_template("login.html")

	# User reached route via POST (as by submitting a form via POST)
	if request.method == "POST":
		username = request.form.get("lusername")
		password = request.form.get("lpassword")

		# Ensure username was submitted
		if not request.form.get("lusername"):
			flash("must provide username")
			return render_template("login.html")

		# Ensure password was submitted
		elif not request.form.get("lpassword"):
			flash("must provide password")
			return render_template("login.html")

		try:

			# Query database for username
			rows = db.execute("SELECT * FROM Users WHERE username = ?", request.form.get("lusername"))

			# Ensure username exists and password is correct
			if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("lpassword")):
				flash("invalid username and/or password")
				return render_template("login.html")

			# Remember which user has logged in
			session["user_id"] = rows[0]["idx"]

			flash(f'Successfully logged in as "{username}"')

			# level 1 user can only view Student and Courses tables
			level = getLevel()
			layout = getLayout(level)
			username = getUserName()

			return render_template(layout, username=username)

		except Exception as e:
			flash(e)
			level = getLevel()
			return render_template("login.html")

	   	# User reached route via GET (as by clicking a link or via redirect)
	else:
		return render_template("login.html")


# --------------- REGISTER ------------------
@app.route("/register", methods=["GET", "POST"])
def register():
	# Forget any user_id
	session.clear()
	fields = []
	# User reached route via POST (by submitting a form via POST)
	if request.method == "POST":

		# Ensure username was submitted
		if not request.form.get("rusername"):
			flash("You need to enter a username")
			return render_template("login.html")

		# Ensure password was submitted
		elif not request.form.get("rpassword"):
			flash("You must provide a password")
			return render_template("login.html")

		# Ensure password and confirmation match
		if not request.form.get("rpassword") == request.form.get("rconfirmpassword"):
			flash("Password was not confirmed")
			return render_template("login.html")

		username = request.form.get("rusername")
		password = request.form.get("rpassword")

		# Check if user name already exists
		rows = db.execute("SELECT username FROM Users")
		for row in rows:
			if username == row['username']:
				flash("User name already exists")
				return render_template("login.html")

		level = 1

		# Generate hash of password
		hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

		fields.append(username)
		fields.append(hash)
		fields.append(level)

      # insert new user into database
		try:
			# Get dataframe from existing users, add new user and write to database

			df = createDF_from_table(level, "Users")


			# Remove 'idx' column since it will be recreated when datatable written to table
			df = df.drop(df.columns[0], axis=1)
			# Add a new row in the dataframe and write to database 'Users' table
			df.loc[len(df)] = fields

			# Create temporary user id so table can be written to database
			session["user_id"] = 1
			writeDFReg_to_SQL(level, df, "Users")

			flash(f"You are now registered as {username}")
			return render_template("login.html")
		except Exception as e:
			flash(f' {e} Unable to register user "{username}"')
			return render_template("login.html")
		finally:
			flash(f"You are now registered as {username}")
			return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
	else:
		return render_template("login.html")


if __name__ == '__main__':
   app.run(debug = True)
