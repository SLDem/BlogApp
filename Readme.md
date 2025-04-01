FastAPI MVC Web Application with MySQL & SQLAlchemy

## Setup Instructions
1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure MySQL Connection:**
   - Ensure MySQL is running (`net start MySQL` or `sudo systemctl start mysql`).
   - Update `DATABASE_URL` in the script with correct credentials.
3. **Run the Server:**
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

### 1. Signup (`POST /signup`)
- Request Body:
  ```json
  {"email": "user@example.com", "password": "securepass"}
  ```
- Response:
  ```json
  {"message": "User created successfully"}
  ```

### 2. Login (`POST /login`)
- Request Body:
  ```json
  {"email": "user@example.com", "password": "securepass"}
  ```
- Response:
  ```json
  {"token": "JWT_TOKEN_HERE"}
  ```

### 3. Add Post (`POST /addpost`)
- Headers: `Authorization: Bearer JWT_TOKEN`
- Request Body:
  ```json
  {"text": "Hello, world!"}
  ```
- Response:
  ```json
  {"postID": 1}
  ```

### 4. Get Posts (`GET /getposts`)
- Headers: `Authorization: Bearer JWT_TOKEN`
- Response:
  ```json
  [{"id": 1, "text": "Hello, world!", "user_id": 1}]
  ```
  (Cached for 5 minutes)

### 5. Delete Post (`DELETE /deletepost`)
- Headers: `Authorization: Bearer JWT_TOKEN`
- Request Params:
  ```json
  {"postID": 1}
  ```
- Response:
  ```json
  {"message": "Post deleted"}
  ```

## Notes
- Uses **JWT-based authentication** for secure access.
- Implements **caching for `GET /getposts` (5 min)**.
- **Error handling included** for invalid requests.

