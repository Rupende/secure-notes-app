# Secure Notes Web App

A secure multi-user notes management web application built with Python and Flask.
The system allows users to register, log in securely, create personal notes, and manage them through a simple dashboard.

This project demonstrates backend development concepts such as authentication, password hashing, database management, session handling, and CRUD operations.

---

## Features

User Authentication

* User registration with unique usernames
* Secure login system
* Password hashing for security
* Session-based authentication
* Logout functionality

Notes Management

* Create personal notes
* View notes on a dashboard
* Delete notes when no longer needed
* Each user can only see their own notes

Security

* Password hashing using bcrypt
* Protected routes for authenticated users only

Application Structure

* Clean Flask project structure
* Template inheritance for reusable layouts
* SQLite database for persistent storage

---

## Project Structure

secure-notes-app
│
├── app.py
├── database.db
│
├── templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
│
└── static
└── style.css

---

## Technologies Used

Python
Flask
Flask-Bcrypt
SQLite
HTML
CSS

---

## Installation

1. Clone the repository

git clone https://github.com/yourusername/secure-notes-app.git

2. Navigate to the project folder

cd secure-notes-app

3. Install dependencies

pip install flask flask-bcrypt

4. Run the application

python app.py

5. Open the browser

http://127.0.0.1:5000

---

## Database Design

Users Table

id – Primary Key
username – Unique username
password – Hashed password

Notes Table

id – Primary Key
user_id – Owner of the note
note – Text content of the note

---

## How the Application Works

1. Users register an account.
2. Passwords are securely hashed before being stored.
3. Users log in using their credentials.
4. A session is created to keep users authenticated.
5. Logged-in users access the dashboard to manage notes.
6. Notes are stored in the SQLite database and linked to the user.

---

## Skills Demonstrated

Backend web development
Authentication systems
Password hashing
Session management
Database design
CRUD operations
Flask project architecture

---

## Future Improvements

Search notes functionality
Edit notes feature
Improved UI design with modern CSS frameworks
Note timestamps
REST API integration

---

## Author

Developed as part of a Python backend development project.
