from flask import Flask, render_template, request, redirect, session, make_response, jsonify
from azure.storage.blob import BlobServiceClient
import os
import bcrypt
from dotenv import load_dotenv
from decorators.token import create_token
from pymongo import MongoClient
from bson import ObjectId  
from pymongo.collection import Collection
from pymongo.database import Database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'

# access your MongoDB Atlas cluster
load_dotenv()
connection_string: str = os.getenv("CONNECTION_STRING")
mongo_client: MongoClient = MongoClient(connection_string)

# add in your database and collection from Atlas
database: Database = mongo_client.get_database("users")
collection: Collection = database.get_collection("Cloud")
collection2: Collection = database.get_collection("blacklist")




# Azure Blob Storage connection setup
connect_str = os.getenv("connect_str")
container_name = "media"
blob_service_client = BlobServiceClient.from_connection_string(conn_str=connect_str)

try:
    container_client = blob_service_client.get_container_client(container_name)
    container_client.get_container_properties()
except Exception as e:
    container_client = blob_service_client.create_container(container_name)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the form data
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        # Check if the username already exists
        existing_user = collection.find_one({"username": username})
        if existing_user:
            return make_response(jsonify({'message': 'Username already exists. Please choose a different username.'}), 409)

       
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        new_user = {
            "name": name,
            "username": username,
            "password": hashed_password,  
            "email": email
        }
        collection.insert_one(new_user)

        return redirect('/index')

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return make_response(jsonify({'message': 'You are already logged in. Please log out before attempting to log in again.'}), 409)

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            token = create_token(user)
            session.clear()
            session['user_id'] = str(user['_id'])
            session['username'] = str(user['username'])
            return redirect("/index")
        else:
            return make_response(jsonify({'message': 'Invalid username or password. Please try again.'}), 401)

    return render_template("login.html")

@app.route('/logout', methods=["GET"])
def logout():
    token = request.headers.get('x-access-token')
    if token:
        
        collection2.insert_one({'token': token})
    
    session.clear()
    return redirect("/")


@app.route("/index", methods=["GET"])
def view_photos():
    if "user_id" not in session:
        return redirect("/login")  
    img_data = []

   
    blob_items = container_client.list_blobs()  
    
    for blob in blob_items:
        blob_client = container_client.get_blob_client(blob=blob.name)
        
        
        user_id = blob.name.split('/')[0]   
        
        # Fetch the user's username
        user = collection.find_one({"_id": ObjectId(user_id)})  # Use ObjectId here
        username = user["username"] if user else "Unknown User"
        
        img_data.append({"img_url": blob_client.url, "username": username})
    
    return render_template("index.html", img_data=img_data)

# Upload photos route (restricted to logged-in users)
@app.route("/upload-photos", methods=["POST"])
def upload_photos():
    # Check if the user is logged in
    if "user_id" not in session:
        return redirect("/login")  # Redirect to login page if not logged in

    user_id = session['user_id']
    filenames = ""

    # Upload the files
    for file in request.files.getlist("photos"):
        try:
            # Save the file in the user-specific folder (with user_id)
            blob_name = f'{user_id}/{file.filename}'
            container_client.upload_blob(blob_name, file)  # Upload file to Azure Blob
            filenames += file.filename + "<br />"
        except Exception as e:
            print("Ignoring duplicate filenames", e)  # Ignore duplicates
    
    return redirect("/index")

@app.route("/")
def homepage():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=True)
