# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

# Flask modules
from flask   import render_template, request, redirect, url_for, flash, json, send_file
from jinja2  import TemplateNotFound

# App modules
from app import app, dbConn, cursor
# from app.models import Profiles
import os

UPLOAD_FOLDER = 'app/static/img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# App main route + generic routing
@app.route('/')
def index():
    return render_template('InventoryHome.html')
@app.route('/form')
def userForm():
    return render_template('addProduct.html')
# creating a destination page after input in /form to route to sucess.html
@app.route('/addproduct', methods=['POST', 'GET'])
def addProduct():
    if request.method == 'POST':
        pname = request.form.get("pname")
        description = request.form.get("pdescription")
        category = request.form.get("pcategory")
        quantity = request.form.get('quantity')
        unitprice = request.form.get('unitPrice')
        
        if 'image' in request.files:
            image = request.files['image']
            # Save the file to the specified upload folder
            if image.filename != '':
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                image.save(image_path)
        else:
            # Handle case where no image is uploaded
            image_path = None

        # Input validation here
        error = False
        if not pname:
            error = True
            flash("Please provide product name.")

        if not description:
            error = True
            flash("Please provide Product Description.")

        if not category:
            error = True
            flash("Please provide product category.")

        try:
            quantity = int(quantity)
            if quantity < 0:
                error = True
                flash("Quantity must be greater than or equal to 0.")
        except ValueError:
            error = True
            flash("Quantity must be a valid number.")

        try:
            unitprice = float(unitprice)
            if unitprice < 0:
                error = True
                flash("Unit price must be greater than or equal to 0.")
        except ValueError:
            error = True
            flash("Unit price must be a valid number.")

        if not error:
            # Insert other product data into the database
            sql = "INSERT INTO Product(ProductName, ProductDescription, ProductCategory, Quantity, UnitPrice, Image) VALUES(%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (pname, description, category, quantity, unitprice, image_path))  # Insert image path into the database
            dbConn.commit()
            flash("Product added successfully.")
            return redirect(url_for('addProduct'))
        else:
            return render_template('addProduct.html', pname=pname, description=description, category=category, quantity=quantity, unitprice=unitprice, image=image)

    else:
        return render_template('addProduct.html')
@app.route('/productchart')
def chart():
    # Retrieve a list of product categories
    sql = "select ProductCategory from Product"
    cursor.execute(sql)
    categories = cursor.fetchall()
    return render_template('setchart.html', categories=categories)

    
@app.route('/chart', methods=['GET'])
def graphProduct():
    category = request.args.get("category")  # Retrieve the selected category ID
    
    # Construct and execute SQL queries to fetch product data based on the selected category ID
    sql1 = "SELECT ProductName AS label, Quantity * UnitPrice AS value, Quantity AS UnitsInStock FROM Product WHERE ProductCategory = %s"
    sql2 = "SELECT ProductName AS label, Quantity AS value FROM Product WHERE ProductCategory = %s"
    
    # Execute SQL queries
    cursor.execute(sql1, (category,))
    productValue = cursor.fetchall()
    cursor.execute(sql2, (category,))
    productQuantity = cursor.fetchall()
    
    # Convert the fetched data into formats suitable for FusionCharts
    chartData1 = json.dumps(productValue)
    chartData2 = json.dumps(productQuantity)
    
    return render_template('ProductChart.html', chartData1=chartData1, chartData2=chartData2)


@app.route('/searchProducts', methods = ['GET'])
def SearchProducts():
    # search for product records for a given supplier id
    category = request.args.get('category')
    
    # search for the product records
    sql = "select * from Product where ProductCategory = %s"
    cursor.execute(sql, category)
    products = cursor.fetchall()
    return render_template('ProductTable.html', products=products)
# route the delete page here
@app.route('/deleteProduct', methods = ['POST','GET'])
def select():
    # Retrieve a list of product categories
    sql = "select ProductCategory from Product"
    cursor.execute(sql)
    categories = cursor.fetchall()
    return render_template("deleteProduct.html", categories=categories)

@app.route('/remove', methods=['POST', 'GET'])
def delete():
    pid = request.form.get("pid", '')
    pname = request.form.get("pname", '')
    category = request.form.get("category", '')

    if request.method == 'POST':
        error = False
        original_pid = pid
        original_pname = pname
        original_category = category

        if not pid:
            error = True
            flash("Please provide product id.")
        if not pname:
            error = True
            flash("Please provide product name.")
        if not category:
            error = True
            flash("Please provide product category.")
        if not error:
            # Check if the product exists in the database with the provided PID, Pname, and category
            sql_check = "select * from Product where ProductID = %s and ProductName = %s and ProductCategory = %s"
            cursor.execute(sql_check, (pid, pname, category))
            product = cursor.fetchone()

            if not product:
                error = True
                flash("Product not found in the database.")
            else:
                # Product exists, proceed with deletion
                sql_delete = "delete from Product where ProductID = %s and ProductName = %s and ProductCategory = %s"
                cursor.execute(sql_delete, (pid, pname, category))
                dbConn.commit()
                flash("Product successfully deleted.")

        if error:
            # Render the deleteProduct.html template directly in case of error
            # Retrieve a list of product categories
            sql = "select ProductCategory from Product"
            cursor.execute(sql)
            categories = cursor.fetchall()
            return render_template("deleteProduct.html", categories=categories, pid=original_pid, pname=original_pname, category=original_category)
        else:
            # If no error, return the template with the same values to retain them
            return render_template("deleteProduct.html", pid=pid, pname=pname, category=category)

    # If it's a GET request, render the deleteProduct.html template with the list of product categories
    sql = "select ProductCategory from Product"
    cursor.execute(sql)
    categories = cursor.fetchall()
    return render_template("deleteProduct.html", categories=categories, pid=pid, pname=pname, category=category)

@app.route('/updateProduct')
def userform():
    return render_template("updateProduct.html")
@app.route('/update', methods=['POST'])
def updateProduct():
    pid = request.form.get("pid")
    pname = request.form.get("pname")
    description = request.form.get("pdescription")
    category = request.form.get("pcategory")
    quantity = request.form.get('quantity')
    unitprice = request.form.get('unitPrice')
    image = request.form.get('image')

    # Input validation
    error = False
    if not pname:
        error = True
        flash("Please provide product name.")
    if not description:
        error = True
        flash("Please provide Product Description.")
    if not category:
        error = True
        flash("Please provide product category.")
    if not quantity:
        error = True
        flash("Please provide product quantity.")
    if not unitprice:
        error = True
        flash("Please provide product unit price.")
    if not image:
        error = True
        flash("Please provide product image.")
    try:
        quantity = int(quantity)
        if quantity < 0:
            error = True
            flash("Quantity must be greater than or equal to 0.")
    except ValueError:
        error = True
        flash("Quantity must be a valid integer.")
    try:
        unitprice = float(unitprice)
        if unitprice < 0:
            error = True
            flash("Unit price must be greater than or equal to 0.")
    except ValueError:
        error = True
        flash("Unit price must be a valid number.")

    if not error:
        # Update the product in the database
        sql = "update Product set ProductName = %s, ProductDescription = %s, ProductCategory = %s, Quantity = %s, UnitPrice = %s, Image = %s where ProductID = %s"
        cursor.execute(sql, (pname, description, category, quantity, unitprice, image, pid))
        dbConn.commit()
        flash("Product successfully updated.")
        return render_template('updateProduct.html')
    else:
        # Return to the update form with entered values if there was an error
        return render_template('updateProduct.html', pid=pid, pname=pname, description=description, category=category, quantity=quantity, unitprice=unitprice, image=image)
@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword')

    # Fetch products containing the keyword in their name
    sql = "select * from Product where ProductName like %s"
    cursor.execute(sql, ('%' + keyword + '%',))
    products = cursor.fetchall()

    if not products:
        # If no products found, render an error message
        return render_template('searchProduct.html', error="Product not found.")
    else:
        # Render the search results
        return render_template('searchProduct.html', products=products)
