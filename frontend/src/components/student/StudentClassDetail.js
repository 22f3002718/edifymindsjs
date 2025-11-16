import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ArrowLeft, Video, FileText, Bell, Calendar, Clock, FolderOpen, ExternalLink, AlertCircle, FileQuestion } from "lucide-react";

const StudentClassDetail = () => {
  const navigate = useNavigate();
  const { classId } = useParams();
  const [classData, setClassData] = useState(null);
  const [homework, setHomework] = useState([]);
  const [notices, setNotices] = useState([]);
  const [resources, setResources] = useState([]);
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClassData();
  }, [classId]);

  const fetchClassData = async () => {
    try {
      const [classRes, hwRes, noticeRes, resourceRes, testsRes] = await Promise.all([
        axios.get(`${API}/classes/${classId}`),
        axios.get(`${API}/classes/${classId}/homework`),
        axios.get(`${API}/classes/${classId}/notices`),
        axios.get(`${API}/classes/${classId}/resources`),
        axios.get(`${API}/classes/${classId}/tests`)
      ]);
      setClassData(classRes.data);
      setHomework(hwRes.data);
      setNotices(noticeRes.data);
      setResources(resourceRes.data);
      setTests(testsRes.data);
    } catch (error) {
      toast.error("Failed to load class information");
    } finally {
      setLoading(false);
    }
  };

  const handleJoinClass = () => {
    if (classData?.zoom_link) {
      window.open(classData.zoom_link, '_blank');
    } else {
      toast.error("No live class link available");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-purple-600 text-xl">Loading...</div>
      </div>
    );
  }

  if (!classData) {
    return (
      <div className="text-center text-gray-600 py-12">Class not found</div>
    );
  }

  return (
    <div className="animate-fadeIn">
      <Button 
        variant="ghost" 
        onClick={() => navigate('/student/dashboard')}
        className="mb-6"
        data-testid="back-to-home"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to My Classes
      </Button>

      {/* Class Header */}
      <Card className="mb-8" style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}>
        <CardHeader>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="text-white">
              <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: 'Poppins, sans-serif' }}>
                {classData.name}
              </h1>
              <Badge className="bg-white text-purple-700 mb-3">
                {classData.grade_level}
              </Badge>
              <p className="text-purple-100 text-lg">{classData.description}</p>
              <div className="flex gap-4 mt-4 text-purple-100">
                <div className="flex items-center">
                  <Calendar className="h-4 w-4 mr-2" />
                  <span>{classData.days_of_week.join(", ")}</span>
                </div>
                <div className="flex items-center">
                  <Clock className="h-4 w-4 mr-2" />
                  <span>{classData.time}</span>
                </div>
              </div>
            </div>
            {classData.zoom_link && (
              <Button 
                size="lg"
                className="bg-white text-purple-700 hover:bg-purple-50 font-bold text-lg px-8 py-6"
                onClick={handleJoinClass}
                data-testid="join-live-class-button"
              >
                <Video className="mr-2 h-6 w-6" />
                Join Live Class
              </Button>
            )}
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Notices */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-2xl" style={{ color: '#7B2CBF' }}>
              <Bell className="mr-2 h-6 w-6" />
              Notices & Announcements
            </CardTitle>
          </CardHeader>
          <CardContent>
            {notices.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No notices yet</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {notices.map((notice) => (
                  <Card 
                    key={notice.id} 
                    className={notice.is_important ? "border-2 border-orange-400" : ""}
                    data-testid={`student-notice-${notice.id}`}
                  >
                    <CardContent className="pt-4">
                      <div className="flex items-start gap-2 mb-1">
                        <h4 className="font-semibold text-lg">{notice.title}</h4>
                        {notice.is_important && (
                          <Badge className="bg-orange-500 text-white text-xs">
                            <AlertCircle className="h-3 w-3 mr-1" />
                            Important
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mb-2">
                        {new Date(notice.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-gray-700">{notice.message}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Homework */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-2xl" style={{ color: '#7B2CBF' }}>
              <FileText className="mr-2 h-6 w-6" />
              Homework
            </CardTitle>
          </CardHeader>
          <CardContent>
            {homework.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No homework assigned yet</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {homework.map((hw) => (
                  <Card key={hw.id} data-testid={`student-homework-${hw.id}`}>
                    <CardContent className="pt-4">
                      <h4 className="font-semibold text-lg mb-1">{hw.title}</h4>
                      <div className="flex items-center text-sm text-gray-600 mb-2">
                        <Calendar className="h-4 w-4 mr-1" />
                        Due: {hw.due_date}
                      </div>
                      <p className="text-gray-700 mb-2">{hw.description}</p>
                      {hw.attachment_link && (
                        <a 
                          href={hw.attachment_link} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-purple-600 hover:text-purple-700 text-sm font-medium"
                          data-testid={`student-homework-link-${hw.id}`}
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          View Attachment
                        </a>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Tests */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl" style={{ color: '#7B2CBF' }}>
              <FileQuestion className="mr-2 h-6 w-6" />
              Tests & Assessments
            </CardTitle>
          </CardHeader>
          <CardContent>
            {tests.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No tests available yet</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {tests.map((test) => (
                  <Card 
                    key={test.id} 
                    className="card-hover"
                    data-testid={`student-test-${test.id}`}
                  >
                    <CardContent className="pt-6">
                      <div className="mb-4">
                        <h4 className="font-semibold text-xl mb-2">{test.title}</h4>
                        <p className="text-gray-600 text-sm mb-3">{test.description}</p>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline">
                            <Clock className="h-3 w-3 mr-1" />
                            {test.duration_minutes} minutes
                          </Badge>
                          <Badge variant="outline">
                            <FileQuestion className="h-3 w-3 mr-1" />
                            {test.questions.length} questions
                          </Badge>
                        </div>
                      </div>
                      <Button
                        onClick={() => navigate(`/student/test/${test.id}`)}
                        className="w-full text-white"
                        style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                        data-testid={`take-test-button-${test.id}`}
                      >
                        <FileQuestion className="mr-2 h-4 w-4" />
                        Take Test
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Resources */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl" style={{ color: '#7B2CBF' }}>
              <FolderOpen className="mr-2 h-6 w-6" />
              Learning Resources
            </CardTitle>
          </CardHeader>
          <CardContent>
            {resources.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No resources available yet</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {resources.map((resource) => (
                  <Card 
                    key={resource.id} 
                    className="card-hover cursor-pointer"
                    onClick={() => window.open(resource.drive_link, '_blank')}
                    data-testid={`student-resource-${resource.id}`}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-start gap-3">
                        {resource.type === "folder" ? (
                          <FolderOpen className="h-10 w-10 text-purple-600 flex-shrink-0" />
                        ) : (
                          <FileText className="h-10 w-10 text-purple-600 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-lg mb-1 break-words">{resource.name}</h4>
                          <Badge variant="secondary" className="text-xs mb-2">
                            {resource.type}
                          </Badge>
                          <div className="flex items-center text-purple-600 text-sm">
                            <ExternalLink className="h-3 w-3 mr-1" />
                            Open
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default StudentClassDetail;
