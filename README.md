# DOJO – Journey of Doing

DOJO is a full-stack task management web application designed to help users organize tasks efficiently, track productivity, and improve workflow management through analytics and personalized task tracking.


## Features

### User Authentication
- Secure user registration and login
- Password encryption and authentication

### Task Management
- Create, update, delete tasks
- Task categorization
- Priority-based task handling

### Notifications
- Task reminder notifications
- Deadline alerts

### Progress Analytics
- Visual productivity tracking
- Progress charts using Chart.js
- Task completion statistics

### Modern UI
- Responsive dashboard
- Dark/Light theme toggle
- Clean and user-friendly interface


## Technologies Used

### Frontend
- HTML
- CSS
- JavaScript
- Bootstrap

### Backend
- Flask (Python)

### Database
- MongoDB

### Libraries & Tools
- Chart.js


## Project Structure

```text
TASK_MANAGER
│
├── static
├── templates
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   ├── progress_analytics.html
│   └── register.html
│
├── venv
├── .gitignore
├── app.py
├── README.md
└── requirements.txt
```


## Installation Guide

### Step 1: Clone Repository

```bash
git clone https://github.com/shrishti-v2/dojo-task-manager.git
```

---

### Step 2: Navigate to Project

```bash
cd DOJO-Task-Management-System
```

---

### Step 3: Backend Setup

```bash
python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
```

Run backend:

```bash
python app.py
```

---

### Step 4: MongoDB Setup

Make sure MongoDB is running locally on:

```bash
mongodb://localhost:27017
```

---

### Step 5: Run Application

Open browser:

```bash
http://localhost:5000
```

---

## Screenshots

### Login Page
![Login](screenshots/login.png)

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Profile Panel
![Profile](screenshots/profile.png)

### Progress Analytics
![Analytics](screenshots/analytics.png)


## Real-world Applications

- Personal productivity management
- Student task tracking
- Team workflow organization
- Project deadline management


## Future Scope

- AI-based task prioritization
- Calendar integration
- Real-time collaboration
- Mobile application support
- Cloud deployment


## Author

**Shrishti Vishwakarma**  
Final Year B.Sc Computer Science Student  
DOJO – Journey of Doing