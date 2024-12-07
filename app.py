from flask import Flask, render_template, request, redirect, jsonify
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId


# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)


# MongoDB (Cosmos DB Mongo API) connection
connection_string = os.getenv("mongoUrl")  
client = MongoClient(connection_string)
database = client.media_dt
posts_collection = database.posts_dt

# Azure Blob Storage connection setup
connect_str = os.getenv("connect_str")  # Blob storage connection string from .env
container_name = "media"  
blob_service_client = BlobServiceClient.from_connection_string(conn_str=connect_str)

try:
    # Ensure the container exists
    container_client = blob_service_client.get_container_client(container_name)
    container_client.get_container_properties()
except Exception:
    # Create the container if it does not exist
    container_client = blob_service_client.create_container(container_name)


@app.route("/")
def homepage():
    """Display all posts from the database."""
    posts = list(posts_collection.find())
    for post in posts:
        post['_id'] = str(post['_id'])  # Convert ObjectId to string for JSON serialization
    return render_template("index.html", posts=posts)


@app.route("/upload", methods=["POST"])
def upload_photo():
    """Upload a photo and save metadata to the database."""
    file = request.files.get("photo")
    caption = request.form.get("caption")

    if not file:
        return jsonify({"message": "No file provided"}), 400

    try:
        # Upload the file to Azure Blob Storage
        blob_name = file.filename
        container_client.upload_blob(blob_name, file)

        # Save metadata in cosmosdb
        new_post = {
            "caption": caption,
            "blob_name": blob_name,
            "blob_url": container_client.get_blob_client(blob_name).url,
        }
        posts_collection.insert_one(new_post)

        return redirect("/")
    except Exception as e:
        return jsonify({"message": f"Failed to upload file: {e}"}), 500


@app.route("/edit/<post_id>", methods=["PUT"])
def edit_caption(post_id):
    """Edit the caption of a post."""
    new_caption = request.form.get("caption")
    if not new_caption:
        return jsonify({"message": "Caption cannot be empty"}), 400

    updated_result = posts_collection.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"caption": new_caption}}
    )

    if updated_result.matched_count == 0:
        return jsonify({"message": "Post not found"}), 404

    return jsonify({"message": "Caption updated successfully"}), 200


@app.route("/delete/<post_id>", methods=["POST"])
def delete_post(post_id):
    """Delete a post and its corresponding blob."""
    if request.form.get('_method') == 'DELETE':
        try:
            post = posts_collection.find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"message": "Post not found"}), 404

            # Delete the blob from Azure Blob Storage
            blob_name = post["blob_name"]
            container_client.delete_blob(blob_name)

            # Delete metadata from MongoDB
            posts_collection.delete_one({"_id": ObjectId(post_id)})

            return jsonify({"message": "Post deleted successfully"}), 200
        except Exception as e:
            return jsonify({"message": f"Failed to delete post: {e}"}), 500


if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True)
