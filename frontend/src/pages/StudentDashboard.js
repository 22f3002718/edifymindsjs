import { useState, useEffect } from "react";
import { Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { API } from "../App";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Home, BookOpen, FileText, Bell, LogOut, ClipboardCheck } from "lucide-react";
import StudentHome from "../components/student/StudentHome";
import StudentClassDetail from "../components/student/StudentClassDetail";
import TakeTest from "../components/student/TakeTest";
import TestResult from "../components/student/TestResult";
import MyTestResults from "../components/student/MyTestResults";

const StudentDashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    toast.success("Goodbye! See you soon!");
    navigate("/");
  };

  const isActive = (path) => {
    return location.pathname.includes(path);
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)' }}>
      {/* Top Navigation */}
      <div className="shadow-lg" style={{ background: 'linear-gradient(90deg, #7B2CBF 0%, #9333ea 100%)' }}>
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="bg-white rounded-xl p-2">
              <img 
                src="https://customer-assets.emergentagent.com/job_3a510027-31fd-46df-a0d7-d59fcd85c43c/artifacts/gjow1soj_image.png" 
                alt="EdifyMinds Junior" 
                className="h-10 w-auto"
              />
            </div>
            <div className="text-white">
              <p className="text-sm opacity-80">Hello,</p>
              <p className="text-lg font-bold">{user?.name}!</p>
            </div>
          </div>
          
          <nav className="flex items-center space-x-2">
            <Link to="/student/dashboard">
              <Button 
                variant="ghost" 
                className={`text-white hover:bg-white/20 ${
                  location.pathname === '/student/dashboard' ? 'bg-white/30' : ''
                }`}
                data-testid="student-nav-home"
              >
                <Home className="mr-2 h-5 w-5" />
                Home
              </Button>
            </Link>
            <Link to="/student/test-results">
              <Button 
                variant="ghost" 
                className={`text-white hover:bg-white/20 ${
                  location.pathname === '/student/test-results' ? 'bg-white/30' : ''
                }`}
                data-testid="student-nav-test-results"
              >
                <ClipboardCheck className="mr-2 h-5 w-5" />
                Test Results
              </Button>
            </Link>
            <Button 
              variant="ghost" 
              className="text-white hover:bg-white/20"
              onClick={handleLogout}
              data-testid="student-logout-button"
            >
              <LogOut className="mr-2 h-5 w-5" />
              Logout
            </Button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/dashboard" element={<StudentHome />} />
          <Route path="/class/:classId" element={<StudentClassDetail />} />
          <Route path="/test/:testId" element={<TakeTest />} />
          <Route path="/test/:testId/result" element={<TestResult />} />
          <Route path="/test-results" element={<MyTestResults />} />
        </Routes>
      </div>
    </div>
  );
};

export default StudentDashboard;
