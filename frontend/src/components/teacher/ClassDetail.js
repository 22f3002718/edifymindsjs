import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ArrowLeft, Users, FileText, Calendar, Bell, Video, Edit, FolderOpen, FileQuestion } from "lucide-react";
import StudentsTab from "./tabs/StudentsTab";
import HomeworkTab from "./tabs/HomeworkTab";
import NoticesTab from "./tabs/NoticesTab";
import ResourcesTab from "./tabs/ResourcesTab";
import TestsTab from "./tabs/TestsTab";

const ClassDetail = () => {
  const navigate = useNavigate();
  const { classId } = useParams();
  const [classData, setClassData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClass();
  }, [classId]);

  const fetchClass = async () => {
    try {
      const response = await axios.get(`${API}/classes/${classId}`);
      setClassData(response.data);
    } catch (error) {
      toast.error("Failed to load class");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-purple-600 text-xl">Loading...</div>
      </div>
    );
  }

  if (!classData) {
    return (
      <div className="p-8">
        <div className="text-center text-gray-600">Class not found</div>
      </div>
    );
  }

  return (
    <div className="p-8 animate-fadeIn">
      <Button 
        variant="ghost" 
        onClick={() => navigate('/teacher/classes')}
        className="mb-6"
        data-testid="back-to-classes"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Classes
      </Button>

      <div className="mb-8">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-4xl font-bold gradient-text mb-2" style={{ fontFamily: 'Poppins, sans-serif' }}>
              {classData.name}
            </h1>
            <Badge 
              className="text-white mb-4" 
              style={{ background: 'linear-gradient(135deg, #9333ea 0%, #c084fc 100%)' }}
            >
              {classData.grade_level}
            </Badge>
            <p className="text-gray-600 max-w-3xl">{classData.description}</p>
          </div>
          <Button
            onClick={() => navigate(`/teacher/class/edit/${classId}`)}
            variant="outline"
            data-testid="edit-class-detail-button"
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit Class
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Calendar className="h-8 w-8 text-purple-600 mr-3" />
                <div>
                  <p className="text-sm text-gray-600">Schedule</p>
                  <p className="font-semibold">{classData.days_of_week.join(", ")}</p>
                  <p className="text-sm text-gray-500">{classData.time}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center">
                <Video className="h-8 w-8 text-purple-600 mr-3" />
                <div>
                  <p className="text-sm text-gray-600">Live Class</p>
                  <p className="font-semibold text-sm">
                    {classData.zoom_link ? "Link Added" : "No Link"}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Tabs defaultValue="students" className="w-full">
        <TabsList className="grid w-full grid-cols-5 mb-6">
          <TabsTrigger value="students" data-testid="students-tab">
            <Users className="mr-2 h-4 w-4" />
            Students
          </TabsTrigger>
          <TabsTrigger value="homework" data-testid="homework-tab">
            <FileText className="mr-2 h-4 w-4" />
            Homework
          </TabsTrigger>
          <TabsTrigger value="tests" data-testid="tests-tab">
            <FileQuestion className="mr-2 h-4 w-4" />
            Tests
          </TabsTrigger>
          <TabsTrigger value="notices" data-testid="notices-tab">
            <Bell className="mr-2 h-4 w-4" />
            Notices
          </TabsTrigger>
          <TabsTrigger value="resources" data-testid="resources-tab">
            <FolderOpen className="mr-2 h-4 w-4" />
            Resources
          </TabsTrigger>
        </TabsList>

        <TabsContent value="students">
          <StudentsTab classId={classId} />
        </TabsContent>

        <TabsContent value="homework">
          <HomeworkTab classId={classId} />
        </TabsContent>

        <TabsContent value="tests">
          <TestsTab classId={classId} />
        </TabsContent>

        <TabsContent value="notices">
          <NoticesTab classId={classId} />
        </TabsContent>

        <TabsContent value="resources">
          <ResourcesTab classId={classId} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ClassDetail;
