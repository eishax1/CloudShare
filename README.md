Multimedia Storage API Endpoints
This API allows users to upload multimedia to Azure Blob Storage, store metadata in Cosmos DB, and manage multimedia records.

Base URL
Local: http://127.0.0.1:5000/
Endpoints
Homepage: Display all posts

URL: /
Method: GET
Description: Displays all uploaded posts with their metadata.
Response: A webpage showing all posts with captions and blob URLs.

Upload a Photo
URL: /upload
Method: POST
Description: Uploads a photo to Azure Blob Storage and saves its metadata in Cosmos DB.
Request Body (Form Data):
photo: The image file to upload.
caption: A caption for the uploaded photo.
Response: Redirects to the homepage on success or returns an error message.
Edit a Caption

URL: /edit/<post_id>
Method: PUT
Description: Updates the caption of a specific post.
Request Body (Form Data):
caption: The new caption text.
Response: A success message or an error message if the post ID is not found.
Delete a Post

URL: /delete/<post_id>
Method: POST (with _method=DELETE)
Description: Deletes a post and its corresponding blob from Azure Blob Storage and removes metadata from Cosmos DB.
Response: A success message or an error message if the deletion fails.
Blob URL Metadata
Each uploaded file's metadata includes:
Blob Name: Name of the file in Azure Blob Storage.
Blob URL: URL to access the blob, e.g., https://<storage_account>.blob.core.windows.net/media/<blob_name>.
How to Access Endpoints
Use tools like Postman, curl, or a browser for GET endpoints.
For file uploads, use a form or Postman to send the POST request.
Ensure the .env file contains valid connection strings for Azure Blob Storage and Cosmos DB.