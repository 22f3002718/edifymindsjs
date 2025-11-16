# EdifyMinds Junior - Learning Management System 🎓

A comprehensive LMS platform for educational institutions with advanced test-taking features.

## 🚀 Quick Start

### Prerequisites
- Node.js 16+ and Yarn
- Python 3.8+
- MongoDB 4.x+

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd edifyminds-junior
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your environment variables
```

3. **Frontend Setup**
```bash
cd frontend
yarn install
cp .env.example .env  # Configure your environment variables
```

4. **Start MongoDB**
```bash
sudo systemctl start mongodb
```

5. **Run the Application**

Terminal 1 (Backend):
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
yarn start
```

Visit: http://localhost:3000

## 📚 Key Features

### For Teachers
- ✅ Create and manage classes
- ✅ Create tests by pasting questions in simple text format
- ✅ Set test duration with countdown timer
- ✅ Auto-grading and instant results
- ✅ Track student submissions and performance
- ✅ Post homework and announcements
- ✅ Share learning resources

### For Students
- ✅ Take tests with countdown timer
- ✅ Navigate between questions (Next/Previous)
- ✅ Auto-submit when time expires
- ✅ View detailed results with answer review
- ✅ Track all test results in one place
- ✅ Access class materials and resources

## 📝 Test Question Format

Teachers can create tests by pasting questions in this simple format:

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
```

**Format Rules:**
- Question line starts with `Q`
- Option lines start with `A)`, `B)`, `C)`, etc.
- Answer line starts with `ANSWER:`
- Different number of options per question (2-6 supported)

## 🌐 Deployment

### Recommended Platforms (Easiest to Hardest):

1. **Render.com** ⭐ Recommended for beginners
2. **Railway.app** - One-command deploy
3. **Vercel (Frontend) + Render (Backend)**
4. **DigitalOcean App Platform**
5. **Heroku**
6. **AWS** (Advanced)

### Quick Deploy to Render:

1. Create account on [Render.com](https://render.com)
2. Connect your GitHub repository
3. Create Web Service for backend (Python)
4. Create Static Site for frontend (Node)
5. Add environment variables
6. Deploy!

**For detailed deployment instructions, see [DOCUMENTATION.md](./DOCUMENTATION.md)**

## 📂 Project Structure

```
edifyminds-junior/
├── backend/
│   ├── server.py           # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── pages/         # Main pages (Login, Dashboards)
│   │   ├── components/    # React components
│   │   └── App.js         # Main app component
│   ├── package.json       # Node dependencies
│   └── .env              # Frontend environment variables
├── DOCUMENTATION.md       # Complete documentation
└── README.md             # This file
```

## 🔐 Environment Variables

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017/
DB_NAME=edifyminds_junior
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🧪 Testing

The application includes:
- Manual testing for all features
- Comprehensive test flow validation
- Edge case handling

## 📖 Documentation

For complete documentation including:
- Detailed installation guide
- API documentation
- Deployment instructions
- Troubleshooting guide

**See [DOCUMENTATION.md](./DOCUMENTATION.md)**

## 🛠 Technology Stack

- **Backend**: FastAPI (Python), MongoDB, JWT Authentication
- **Frontend**: React 19, Tailwind CSS, Radix UI
- **Deployment**: Flexible (Render, Railway, Vercel, AWS, etc.)

## 🎯 Default Credentials

For testing purposes, a default teacher account is created:
- **Email**: edify@gmail.com
- **Password**: edify123

## 🐛 Troubleshooting

**Backend won't start:**
```bash
sudo systemctl status mongodb
tail -f /var/log/supervisor/backend.err.log
```

**Frontend won't start:**
```bash
rm -rf node_modules yarn.lock && yarn install
```

**See [DOCUMENTATION.md](./DOCUMENTATION.md) for more troubleshooting**

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Happy Teaching and Learning! 🚀📚**
