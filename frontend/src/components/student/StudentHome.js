import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { BookOpen, Calendar, Clock, Video, Sparkles } from "lucide-react";

const StudentHome = () => {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API}/classes`);
      setClasses(response.data);
    } catch (error) {
      toast.error("Failed to load classes");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-purple-600 text-xl">Loading your classes...</div>
      </div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <div className="mb-8">
        <h1 className="text-5xl font-bold gradient-text mb-3" style={{ fontFamily: 'Poppins, sans-serif' }}>
          My Classes
        </h1>
        <p className="text-gray-600 text-lg">Welcome back! Ready to learn something new today?</p>
      </div>

      {classes.length === 0 ? (
        <Card className="p-16 text-center">
          <div className="text-gray-400">
            <BookOpen className="h-24 w-24 mx-auto mb-6" />
            <h3 className="text-3xl font-semibold mb-3">No Classes Yet</h3>
            <p className="text-lg">You're not enrolled in any classes. Please contact your teacher to get started!</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classes.map((classItem) => (
            <Card 
              key={classItem.id} 
              className="card-hover cursor-pointer border-2 border-purple-100 overflow-hidden"
              onClick={() => navigate(`/student/class/${classItem.id}`)}
              data-testid={`student-class-card-${classItem.id}`}
              style={{
                background: 'linear-gradient(135deg, #ffffff 0%, #faf5ff 100%)'
              }}
            >
              <div 
                className="h-3" 
                style={{ background: 'linear-gradient(90deg, #7B2CBF 0%, #c084fc 100%)' }}
              />
              <CardHeader className="pb-3">
                <div className="flex items-start gap-3 mb-2">
                  <div className="bg-purple-100 rounded-full p-3">
                    <BookOpen className="h-8 w-8 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-2xl mb-2" style={{ color: '#7B2CBF' }}>
                      {classItem.name}
                    </CardTitle>
                    <Badge 
                      className="text-white"
                      style={{ background: 'linear-gradient(135deg, #9333ea 0%, #c084fc 100%)' }}
                    >
                      {classItem.grade_level}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 mb-4 line-clamp-2">
                  {classItem.description}
                </p>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center text-gray-700">
                    <Calendar className="h-4 w-4 mr-2 text-purple-600" />
                    <span className="font-medium">{classItem.days_of_week.join(", ")}</span>
                  </div>
                  <div className="flex items-center text-gray-700">
                    <Clock className="h-4 w-4 mr-2 text-purple-600" />
                    <span className="font-medium">{classItem.time}</span>
                  </div>
                  {classItem.zoom_link && (
                    <div className="flex items-center text-green-600">
                      <Video className="h-4 w-4 mr-2" />
                      <span className="font-medium">Live Class Available</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default StudentHome;
