import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


# The login, logout and error handling functions as well as the configuration settings are from the pset#9 source code. I also reused the login and register functions that I wrote for pset#9
# The helpers functions are also from the pset#9 source code

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///recipe.db")

# Route for home page
@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":

        # Get the recipe the user wishes to see
        recipe = request.form.get("recipe")

        # Select the ingredients for the recipe the user wishes to see
        rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

        # Select the instructions for the recipe the user wishes to see
        rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

        # Render the recipe card for the recipe the user wishes to see
        return render_template("recipe_card.html", rows=rows, rows2=rows2, recipe=recipe)

    else:

        # Get the current user's recipes
        rows = db.execute("SELECT DISTINCT recipe FROM ingredients WHERE user_id = :id",
                          id=session["user_id"])

        # Return the home page with the appropriate select options for the current user's recipes
        return render_template("home.html", rows=rows)


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":

        # Get the number of ingredients and the number of instructions for the recipe
        ingredients = request.form.get("ingredients")
        instructions = request.form.get("steps")

        # Convert the returned strings to integers
        number = int(ingredients)
        steps = int(instructions)

        # Return the page containing the correct number of forms for the desired ingredients and steps
        return render_template("new.html", number=number, steps=steps)

    else:

        # Return the page where the user will specify how many steps and ingredients they want for the new recipe
        return render_template("create.html")


@app.route("/new", methods=["POST"])
@login_required
def new():

    # Get the number of steps, the number of ingredients and the name of the recipe from the submitted form
    number = request.form.get("number")
    steps = request.form.get("steps")
    recipe = request.form.get("recipe")

    # Iterate over the number of input ingredients and add each ingredient, the associated amount and the associated unit to the ingredients table
    for i in range(1,int(number)+1):
        ingredient = request.form.get(f"ingredient{i}")
        amount = request.form.get(f"amount{i}")
        unit = request.form.get(f"unit{i}")
        db.execute("INSERT INTO ingredients (user_id, recipe, ingredient, amount, unit) VALUES (?,?,?,?,?)",
                   session["user_id"], recipe, ingredient, amount, unit)

    # Iterate over the number of input instructions and add each instruction to the instructions table
    for i in range(1,int(steps)+1):
        step = request.form.get(f"step{i}")
        db.execute("INSERT INTO instructions (user_id, recipe, step) VALUES (?,?,?)",
                   session["user_id"], recipe, step)

    # Redirect user to home page
    return redirect("/")


@app.route("/recipes", methods=["GET"])
@login_required
def recipes():

    # Select the all the current user's recipes
    rows = db.execute("SELECT DISTINCT recipe FROM ingredients WHERE user_id = :id",
                      id=session["user_id"])

    # Return the page displaying a list of all these recipes
    return render_template("recipes.html", rows=rows)

@app.route("/edit", methods=["POST"])
@login_required
def edit():

    # Get the value of the button called action that the user clicked on the recipe list page
    actions = request.form.get("action")

    # Split the returned string to determine if the button cliked was edit or delete
    action = actions.split()[1]

    # If the button was a delete button, then select all the ingredients and instructions associated with that recipe and that user and delete them from the ingredients and instructions tables respectively
    if action == "delete":

        # Partition the returned string to get the title of the recipe the user wishes to delete
        recipe = actions.partition(' delete')[0]

        db.execute("DELETE FROM ingredients WHERE user_id = :id and recipe = :recipe",
                   id=session["user_id"], recipe=recipe)

        db.execute("DELETE FROM instructions WHERE user_id = :id and recipe = :recipe",
                   id=session["user_id"], recipe=recipe)

        # Redirect user to home page
        return redirect("/")

    # If the user cliked the edit button:
    else:

        # Partition the returned string to get the title of the recipe the user wishes to edit
        recipe = actions.partition(' edit')[0]

        # Select the ingredients for the recipe the user selected
        rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

        # Select the instructions for the recipe the user selected
        rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

        # Return the edit page displaying all the ingredients and instructions for the selected recipe
        return render_template("edit.html", rows=rows, rows2=rows2, recipe=recipe)

@app.route("/edit_recipe", methods=["POST"])
@login_required
def edit_recipe():

    # Request the value of the add button from the submited form
    add = request.form.get("add")

    # If the returned value is not None, this means the user has cliked the add button and wants to add an ingredient or instruction to this recipe
    if add != None:

        # Request the value of the hidden input contianing the name of the recipe the user is editing
        recipe = request.form.get("recipe")
        # Request the value of the hidden input contianing the type of item, either ingredient or step, the user wishes to add
        item_type = request.form.get("item_type")

        # If the item is an ingredient:
        if item_type == "ingredient":

            # Request the name of the new ingredient, amount and unit from the submitted form
            ingredient = request.form.get("ingredient")
            amount = request.form.get("amount")
            unit = request.form.get("unit")

            # Insert the new ingredient, amount and unit into the ingredients table with the appropriate recipe association
            db.execute("INSERT INTO ingredients (user_id, recipe, ingredient, amount, unit) VALUES (?,?,?,?,?)",
                       session["user_id"], recipe, ingredient, amount, unit)

            # Select the ingredients for the recipe the user is currently editing
            rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Select the instructions for the recipe the user is currently editing
            rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Return the edit page for the recipe the user is currently editing
            return render_template("edit.html", rows=rows, rows2=rows2, recipe=recipe)

        # If the item type is not ingredient, it must be an instruction
        else:

            # Request the new instruction from the submitted form
            step = request.form.get("step")

            # Insert the new instruction into the instructions table with the appropriate recipe association
            db.execute("INSERT INTO instructions (user_id, recipe, step) VALUES (?,?,?)",
                       session["user_id"], recipe, step)

            # Select the ingredients for the recipe the user is currently editing
            rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Select the instructions for the recipe the user is currently editing
            rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Return the edit page for the recipe the user is currently editing
            return render_template("edit.html", rows=rows, rows2=rows2, recipe=recipe)


    # If the value of the add button is none, this means the user wants to edit or delete an existing ingredient or instruction

    # Request the value of the action button from the submitted form
    actions = request.form.get("action")

    # If action does not return none, this means the user clicked the delete button for an exisiting ingredient or instruction
    if actions != None:

        # Partition and split the returned string to get the name of the recipe the user is currently editing and the type of item the user wishes to delete
        item_type = actions.split()[3]
        print(item_type)
        recipe = actions.partition(" delete")[0]

        # If the type of item is an ingredient:
        if item_type =="ingredient":

            # Partition the returned string after the item type to get a string containg only the ingedient name
            # The space after ingredient ensures that the resulting string does not begin with a space
            item = actions.partition('ingredient ')[2]

            # Delete the appropriate ingredient along with its amount and unit from the recipe the user is currently editing
            db.execute("DELETE FROM ingredients WHERE user_id = :id and recipe = :recipe and ingredient = :item",
                   id=session["user_id"], recipe=recipe, item=item)

            # Select the ingredients for the recipe the user is currently editing
            rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Select the instructions for the recipe the user is currently editing
            rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Return the edit page for the recipe the user is currently editing
            return render_template("edit.html", rows=rows, rows2=rows2, recipe=recipe)

        # If the item type is not an ingredient, it must be an instruction
        else:

            # Partition the returned string after the item type to get a string containg only the instruction name
            # The space after step ensures that the resulting string does not begin with a space
            item = actions.partition('step ')[2]

            # Delete the appropriate instruction from the recipe the user is currently editing
            db.execute("DELETE FROM instructions WHERE user_id = :id and recipe = :recipe and step = :item",
                   id=session["user_id"], recipe=recipe, item=item)

            # Select the ingredients for the recipe the user is currently editing
            rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Select the instructions for the recipe the user is currently editing
            rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Return the edit page for the recipe the user is currently editing
            return render_template("edit.html", rows=rows, rows2=rows2, recipe=recipe)

    # If action returns none, this means the user clicked the edit button for an exisiting ingredient or instruction
    else:

        # Request the value of the hidden input contianing the type of item, either ingredient or step, the user wishes to edit
        item_type = request.form.get("item_type")
        # Request the value of the hidden input contianing the name of the recipe the user is currently editing
        recipe = request.form.get("recipe")

        # If the item type is ingredient:
        if item_type == "ingredient":

            # Get the user input information containing the updated ingredient, amount and unit
            item = request.form.get("item")
            ingredient = request.form.get("ingredient")
            amount = request.form.get("amount")
            unit = request.form.get("unit")

            # Update the existing ingredient for the recipe the user is currently editing to reflect the new user input
            db.execute("UPDATE ingredients SET ingredient = :ingredient, amount = :amount, unit = :unit WHERE user_id = :id and recipe = :recipe and ingredient = :item",
                       ingredient=ingredient, amount=amount, unit=unit, id=session["user_id"], recipe=recipe, item=item)

            # Select the ingredients for the recipe the user is currently editing
            rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Select the instructions for the recipe the user is currently editing
            rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Return the edit page for the recipe the user is currently editing
            return render_template("edit.html", rows=rows, rows2=rows2, recipe=recipe)

        # If the item type is not ingredient the user must wish to edit an instruction
        else:

            # Get the user input information containing the updated instruction
            item = request.form.get("item")
            step = request.form.get("step")

            # Update the existing instruction for the recipe the user is currently editing to reflect the new user input
            db.execute("UPDATE instructions SET step = :step WHERE user_id = :id and recipe = :recipe and step = :item",
                       step=step, id=session["user_id"], recipe=recipe, item=item)

            # Select the ingredients for the recipe the user is currently editing
            rows = db.execute("SELECT ingredient, amount, unit FROM ingredients WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Select the instructions for the recipe the user is currently editing
            rows2 = db.execute("SELECT step FROM instructions WHERE user_id = :id and recipe = :recipe",
                      id=session["user_id"], recipe=recipe)

            # Return the edit page for the recipe the user is currently editing
            return render_template("edit.html", rows=rows, rows2=rows2, recipe=recipe)


@app.route("/grocery_list", methods=["GET","POST"])
@login_required
def grocery_list():

    if request.method == "POST":

        # Request the value of the button called action containing the name of the grocery list item associated with the clicked button
        action = request.form.get("action")

        # If action does not return none, this means the user wishes to delete an item from the grocery list
        if action != None:

            # Delete the selected item from the current user's grocery list
            db.execute("DELETE FROM grocerylist WHERE user_id = :id and item = :item",
                   id=session["user_id"], item=action)

            # Select all the current user's grocery list items
            rows = db.execute("SELECT DISTINCT item FROM grocerylist WHERE user_id = :id",
                      id=session["user_id"])

            # Return the grocery list page displaying all the items on the current user's grocery list
            return render_template("grocery_list.html", rows=rows)

        # If action returns none, this means the user is trying to add items to the grocery list
        else:

            # Request a list of all the items for which the user clicked the associated checkbox
            items = request.form.getlist('checkbox')

            # Loop over the length of the list and add each item to the grocery list table
            for i in range(len(items)):
                item = items[i]

                db.execute("INSERT INTO grocerylist (user_id, item) VALUES (?,?)",
                           session["user_id"], item)

            # Select all the current user's grocery list items
            rows = db.execute("SELECT DISTINCT item FROM grocerylist WHERE user_id = :id",
                          id=session["user_id"])

            # Return the grocery list page displaying all the items on the current user's grocery list
            return render_template("grocery_list.html", rows=rows)

    else:

        # Select all the current user's grocery list items
        rows = db.execute("SELECT DISTINCT item FROM grocerylist WHERE user_id = :id",
                          id=session["user_id"])

        # Return the grocery list page displaying all the items on the current user's grocery list
        return render_template("grocery_list.html", rows=rows)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Ensure pasword and re-entered paswords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("your passwords do not match", 403)

        else:
            # Check to make sure the username is not taken
            taken = db.execute("SELECT username FROM users WHERE username = :username",
                               username=request.form.get("username"))

            if len(taken) != 0:
                return apology("Oops, this username is already taken!", 403)

            # Hash the new user's password
            hash = generate_password_hash(request.form.get("password"))

            # Get the new user's username
            user = request.form.get("username")

            # Insert the new user's information into the database
            db.execute("INSERT INTO users (username, hash) VALUES (?,?)",
                       user, hash)

            # Redirect user to home page
            return redirect("/")

    else:
        return render_template("register.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
