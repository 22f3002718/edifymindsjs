import { useState, useEffect } from "react";
import { Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { API } from "../App";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Home, BookOpen, Calendar, FileText, Bell, LogOut, Users, Plus } from "lucide-react";
import ClassesOverview from "../components/teacher/ClassesOverview";
import CreateEditClass from "../components/teacher/CreateEditClass";
import ClassDetail from "../components/teacher/ClassDetail";

const TeacherDashboard = () => {
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
    toast.success("Logged out successfully");
    navigate("/");
  };

  const isActive = (path) => {
    return location.pathname.includes(path);
  };

  return (
    <div className="flex h-screen" style={{ background: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)' }}>
      {/* Sidebar */}
      <div className="w-64 shadow-2xl" style={{ background: 'linear-gradient(180deg, #7B2CBF 0%, #9333ea 100%)' }}>
        <div className="p-6">
          <div className="bg-white rounded-2xl p-4 mb-8">
            <img 
              src="https://customer-assets.emergentagent.com/job_3a510027-31fd-46df-a0d7-d59fcd85c43c/artifacts/gjow1soj_image.png" 
              alt="EdifyMinds Junior" 
              className="w-full h-auto"
            />
          </div>
          
          <div className="text-white mb-8">
            <p className="text-sm opacity-80">Welcome back,</p>
            <p className="text-lg font-bold">{user?.name}</p>
          </div>

          <nav className="space-y-2">
            <Link to="/teacher/dashboard" data-testid="nav-dashboard">
              <Button 
                variant="ghost" 
                className={`w-full justify-start text-white hover:bg-white/20 ${
                  isActive('/teacher/dashboard') && !location.pathname.includes('/class/') ? 'bg-white/30' : ''
                }`}
              >
                <Home className="mr-3 h-5 w-5" />
                Dashboard
              </Button>
            </Link>
            <Link to="/teacher/classes" data-testid="nav-classes">
              <Button 
                variant="ghost" 
                className={`w-full justify-start text-white hover:bg-white/20 ${
                  isActive('/teacher/classes') ? 'bg-white/30' : ''
                }`}
              >
                <BookOpen className="mr-3 h-5 w-5" />
                Classes
              </Button>
            </Link>
          </nav>
        </div>

        <div className="absolute bottom-0 w-64 p-6">
          <Button 
            variant="ghost" 
            className="w-full justify-start text-white hover:bg-white/20"
            onClick={handleLogout}
            data-testid="logout-button"
          >
            <LogOut className="mr-3 h-5 w-5" />
            Logout
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <Routes>
          <Route path="/dashboard" element={<ClassesOverview />} />
          <Route path="/classes" element={<ClassesOverview />} />
          <Route path="/class/create" element={<CreateEditClass />} />
          <Route path="/class/edit/:classId" element={<CreateEditClass />} />
          <Route path="/class/:classId" element={<ClassDetail />} />
        </Routes>
      </div>
    </div>
  );
};

export default TeacherDashboard;
