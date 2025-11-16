# EdifyMinds Junior - Complete Documentation

## 📚 Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Prerequisites](#prerequisites)
5. [Installation & Setup](#installation--setup)
6. [Environment Variables](#environment-variables)
7. [Running the Application](#running-the-application)
8. [Testing Module Guide](#testing-module-guide)
9. [Deployment Guide](#deployment-guide)
10. [API Documentation](#api-documentation)
11. [Troubleshooting](#troubleshooting)

---

## 🎓 Project Overview

EdifyMinds Junior is a comprehensive Learning Management System (LMS) designed for educational institutions. It provides a platform for teachers to manage classes, create tests, assign homework, and track student progress, while students can access classes, take tests, submit homework, and view their results.

### Key Highlights
- **Role-based access**: Separate interfaces for Teachers and Students
- **Real-time test taking**: Countdown timer with auto-submission
- **Instant results**: Detailed answer review after test submission
- **Class management**: Create and manage multiple classes
- **Resource sharing**: Share learning materials via Google Drive links

---

## ✨ Features

### For Teachers 👨‍🏫
- **Class Management**
  - Create, edit, and delete classes
  - Set class schedules (days and time)
  - Add Zoom links for live classes
  - Integrate Google Drive folders

- **Student Management**
  - Enroll students in classes
  - View all enrolled students
  - Remove students from classes

- **Test Creation**
  - Paste questions in a simple text format
  - System automatically parses questions
  - Set test duration
  - View all student submissions
  - Track student performance

- **Content Management**
  - Post homework assignments with attachments
  - Create notices and announcements
  - Mark important notices
  - Share learning resources

### For Students 👨‍🎓
- **Class Access**
  - View all enrolled classes
  - Join live Zoom classes
  - Access class materials and resources

- **Test Taking**
  - Take tests with countdown timer
  - Navigate between questions (Next/Previous)
  - Auto-submit when time expires
  - Cannot see correct answers until submission

- **Results & Progress**
  - View detailed test results
  - See score and percentage
  - Review each question with correct answers
  - Track all test results in one place

- **Homework & Resources**
  - View assigned homework
  - Access learning resources
  - Read notices and announcements

---

## 🛠 Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB (Motor async driver)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Server**: Uvicorn ASGI server

### Frontend
- **Framework**: React 19
- **Routing**: React Router DOM v7
- **UI Library**: Radix UI + Tailwind CSS
- **State Management**: React Hooks (useState, useEffect)
- **HTTP Client**: Axios
- **Icons**: Lucide React

### DevOps
- **Process Manager**: Supervisord
- **Reverse Proxy**: Nginx (optional for production)

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: v16.x or higher
- **Python**: 3.8 or higher
- **MongoDB**: 4.x or higher
- **Yarn**: Package manager (npm can also be used)
- **Git**: For version control

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd edifyminds-junior
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables section)
touch .env
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
yarn install
# OR
npm install

# Create .env file (see Environment Variables section)
touch .env
```

### 4. MongoDB Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB (Ubuntu/Debian)
sudo apt-get install -y mongodb

# Start MongoDB service
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

**Option B: MongoDB Atlas (Cloud)**
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Get your connection string
4. Use it in the backend .env file

---

## 🔐 Environment Variables

### Backend (.env)

Create `/app/backend/.env` with the following:

```env
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017/
DB_NAME=edifyminds_junior

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# CORS Configuration (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Server Configuration
HOST=0.0.0.0
PORT=8001
```

### Frontend (.env)

Create `/app/frontend/.env` with the following:

```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Or for production (use your deployed backend URL)
# REACT_APP_BACKEND_URL=https://your-backend-domain.com
```

---

## 🏃 Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # If using virtual environment
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
# OR
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Documentation: http://localhost:8001/docs

### Using Supervisord (Production-like)

If you're using supervisord (already configured in the project):

```bash
# Start all services
sudo supervisorctl start all

# Check status
sudo supervisorctl status

# Restart specific service
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Stop all services
sudo supervisorctl stop all
```

---

## 📝 Testing Module Guide

### Question Format

The test module uses a simple text format for question input. Here's the specification:

#### Format Rules:
1. **Question Line**: Starts with `Q` (case-insensitive)
   - Example: `Q1. What is 2 + 2?` or `Q. Capital of France?`

2. **Option Lines**: Start with a letter followed by `)` or `.`
   - Supported: A), B), C), D), E), F)
   - Example: `A) Paris`, `B) London`

3. **Answer Line**: Starts with `ANSWER:` followed by the correct option letter
   - Example: `ANSWER: A` or `ANSWER: B`

4. **Separation**: Leave blank lines between questions (optional but recommended)

#### Example Test Format:

```
Q1. What is the capital of France?
A) London
B) Berlin
C) Paris
D) Madrid
ANSWER: C

Q2. What is 2 + 2?
A) 3
B) 4
C) 5
D) 6
ANSWER: B

Q3. Which planet is known as the Red Planet?
A) Venus
B) Mars
C) Jupiter
D) Saturn
ANSWER: B
```

#### Flexible Options:
- You can have different numbers of options for each question (2-6 options)
- Question numbering is flexible (Q1, Q2, or just Q)
- Case-insensitive parsing

### Test Flow

1. **Teacher Creates Test**
   - Navigate to class details
   - Click "Create Test"
   - Enter title, description, and duration
   - Paste questions in the specified format
   - System automatically parses and validates

2. **Student Takes Test**
   - Navigate to class details
   - Click "Take Test" on available test
   - Countdown timer starts automatically
   - Answer questions one at a time
   - Use Next/Previous to navigate
   - Submit manually or wait for auto-submit

3. **Auto-Submit Feature**
   - When timer reaches 0, test auto-submits
   - Students cannot extend time
   - All answered questions are saved

4. **View Results**
   - After submission, students immediately see:
     - Total score and percentage
     - Number of correct/incorrect answers
     - Detailed review of each question
     - Their selected answer vs correct answer
   - Students can access all past results from "Test Results" menu

---

## 🌐 Deployment Guide

### Recommended Platforms

#### 1. **Render.com** (Easiest - Recommended for Beginners)

**Backend Deployment:**
```yaml
# render.yaml
services:
  - type: web
    name: edifyminds-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: MONGO_URL
        sync: false
      - key: DB_NAME
        value: edifyminds_junior
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: CORS_ORIGINS
        sync: false
```

**Frontend Deployment:**
```yaml
  - type: web
    name: edifyminds-frontend
    runtime: node
    buildCommand: yarn install && yarn build
    startCommand: yarn global add serve && serve -s build -l $PORT
    envVars:
      - key: REACT_APP_BACKEND_URL
        value: https://edifyminds-backend.onrender.com
```

**Steps:**
1. Create account on [Render.com](https://render.com)
2. Connect your GitHub repository
3. Create a new Web Service for backend
4. Create a new Static Site for frontend
5. Set environment variables in Render dashboard
6. Deploy!

#### 2. **Railway.app** (Very Easy)

**Steps:**
1. Install Railway CLI: `npm i -g @railway/cli`
2. Login: `railway login`
3. Initialize: `railway init`
4. Deploy backend:
   ```bash
   cd backend
   railway up
   ```
5. Deploy frontend:
   ```bash
   cd frontend
   railway up
   ```
6. Add MongoDB service from Railway marketplace
7. Set environment variables in Railway dashboard

#### 3. **Vercel (Frontend) + Render/Railway (Backend)**

**Frontend on Vercel:**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel

# Set environment variable
vercel env add REACT_APP_BACKEND_URL
```

**Backend on Render:** (See Render.com steps above)

#### 4. **DigitalOcean App Platform**

**Steps:**
1. Create account on [DigitalOcean](https://www.digitalocean.com)
2. Go to App Platform
3. Connect your GitHub repository
4. Configure two components:
   - Backend (Python/FastAPI)
   - Frontend (Node.js/React)
5. Add MongoDB Managed Database
6. Set environment variables
7. Deploy

#### 5. **Heroku** (Classic Option)

**Backend:**
```bash
# Create Procfile
echo "web: uvicorn server:app --host 0.0.0.0 --port $PORT" > Procfile

# Deploy
heroku create edifyminds-backend
heroku addons:create mongolab
git push heroku main
```

**Frontend:**
```bash
# Deploy
heroku create edifyminds-frontend
heroku buildpacks:add heroku/nodejs
git push heroku main
```

#### 6. **AWS (Advanced)**

**Components:**
- **Frontend**: S3 + CloudFront
- **Backend**: EC2 or Elastic Beanstalk
- **Database**: MongoDB Atlas or DocumentDB

**Steps:**
1. Create S3 bucket for frontend
2. Enable static website hosting
3. Upload build files: `aws s3 sync build/ s3://your-bucket`
4. Create CloudFront distribution
5. Deploy backend to EC2/Elastic Beanstalk
6. Configure security groups and load balancers

### MongoDB Options for Production

1. **MongoDB Atlas** (Recommended)
   - Free tier available
   - Managed service
   - Automatic backups
   - Get connection string: `mongodb+srv://user:pass@cluster.mongodb.net/dbname`

2. **Railway MongoDB**
   - Easy integration with Railway
   - One-click add

3. **Self-hosted**
   - Install on VPS (DigitalOcean, Linode, etc.)
   - More control but requires maintenance

### Environment Variables for Production

**Backend:**
```env
MONGO_URL=your-production-mongodb-url
DB_NAME=edifyminds_junior_prod
JWT_SECRET_KEY=super-secure-random-string
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**Frontend:**
```env
REACT_APP_BACKEND_URL=https://your-backend-domain.com
```

### SSL/HTTPS

Most modern platforms (Render, Vercel, Railway, Heroku) provide free SSL certificates automatically. If deploying to a VPS:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 📡 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe",
  "role": "student",
  "parent_contact": "+1234567890"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "student"
  }
}
```

### Test Endpoints

#### Create Test (Teacher Only)
```http
POST /api/tests
Authorization: Bearer <token>
Content-Type: application/json

{
  "class_id": "class-uuid",
  "title": "Math Quiz - Chapter 5",
  "description": "Test on algebra",
  "duration_minutes": 30,
  "questions_text": "Q1. What is 2+2?\nA) 3\nB) 4\nC) 5\nANSWER: B"
}
```

#### Get Test (Students see without correct answers)
```http
GET /api/tests/{test_id}
Authorization: Bearer <token>
```

#### Submit Test
```http
POST /api/tests/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "test_id": "test-uuid",
  "answers": [
    {
      "question_index": 0,
      "selected_answer": "B"
    },
    {
      "question_index": 1,
      "selected_answer": "A"
    }
  ]
}
```

#### Get Test Result
```http
GET /api/tests/{test_id}/result
Authorization: Bearer <token>
```

#### Get All My Test Results (Student)
```http
GET /api/my-test-results
Authorization: Bearer <token>
```

### Class Endpoints

#### Create Class (Teacher)
```http
POST /api/classes
Authorization: Bearer <token>
```

#### Get All Classes
```http
GET /api/classes
Authorization: Bearer <token>
```

For complete API documentation, visit: `http://localhost:8001/docs` (when backend is running)

---

## 🔧 Troubleshooting

### Common Issues

#### Backend won't start
```bash
# Check if MongoDB is running
sudo systemctl status mongodb

# Check backend logs
tail -f /var/log/supervisor/backend.err.log

# Verify Python dependencies
pip install -r requirements.txt
```

#### Frontend won't start
```bash
# Clear node modules and reinstall
rm -rf node_modules yarn.lock
yarn install

# Check for port conflicts
lsof -i :3000
kill -9 <PID>
```

#### Database connection errors
```bash
# Test MongoDB connection
mongosh

# Check MONGO_URL in backend/.env
# Ensure MongoDB is running and accessible
```

#### CORS errors
- Check `CORS_ORIGINS` in backend/.env
- Ensure frontend URL is included
- In production, update with actual domain

#### JWT token errors
- Check `JWT_SECRET_KEY` in backend/.env
- Clear browser localStorage and login again
- Ensure token is being sent in Authorization header

#### Test parsing errors
- Verify question format strictly follows the specification
- Check that ANSWER line has correct format
- Ensure options use supported letters (A-F)

### Debug Mode

Enable debug logging in backend:
```python
# server.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check browser console for frontend errors:
- Press F12 in browser
- Go to Console tab
- Look for red error messages

---

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review API docs at `/docs` endpoint
3. Check browser console for frontend errors
4. Check backend logs for API errors
5. Ensure all environment variables are set correctly

---

## 📄 License

This project is licensed under the MIT License.

---

## 🎉 Congratulations!

You now have a fully functional Learning Management System with comprehensive test-taking capabilities. Happy teaching and learning! 🚀📚
