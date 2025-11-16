import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Edit, Trash2, Users, Calendar, Clock, BookOpen } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const ClassesOverview = () => {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteClassId, setDeleteClassId] = useState(null);
  const [enrollments, setEnrollments] = useState({});

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      const response = await axios.get(`${API}/classes`);
      setClasses(response.data);
      
      // Fetch student count for each class
      const enrollmentCounts = {};
      for (const cls of response.data) {
        const studentsRes = await axios.get(`${API}/classes/${cls.id}/students`);
        enrollmentCounts[cls.id] = studentsRes.data.length;
      }
      setEnrollments(enrollmentCounts);
    } catch (error) {
      toast.error("Failed to load classes");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (classId) => {
    try {
      await axios.delete(`${API}/classes/${classId}`);
      toast.success("Class deleted successfully");
      setClasses(classes.filter(c => c.id !== classId));
      setDeleteClassId(null);
    } catch (error) {
      toast.error("Failed to delete class");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-purple-600 text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-8 animate-fadeIn">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold gradient-text mb-2" style={{ fontFamily: 'Poppins, sans-serif' }}>
            My Classes
          </h1>
          <p className="text-gray-600">Manage your online classes and students</p>
        </div>
        <Button 
          onClick={() => navigate('/teacher/class/create')}
          className="text-white font-semibold"
          style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
          data-testid="create-class-button"
        >
          <Plus className="mr-2 h-5 w-5" />
          Create New Class
        </Button>
      </div>

      {classes.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-gray-400 mb-4">
            <BookOpen className="h-20 w-20 mx-auto mb-4" />
            <h3 className="text-2xl font-semibold mb-2">No classes yet</h3>
            <p>Create your first class to get started!</p>
          </div>
          <Button 
            onClick={() => navigate('/teacher/class/create')}
            className="text-white font-semibold"
            style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
          >
            <Plus className="mr-2 h-5 w-5" />
            Create Class
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classes.map((classItem) => (
            <Card 
              key={classItem.id} 
              className="card-hover cursor-pointer border-2 border-purple-100"
              onClick={() => navigate(`/teacher/class/${classItem.id}`)}
              data-testid={`class-card-${classItem.id}`}
            >
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-xl mb-2" style={{ color: '#7B2CBF' }}>
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
                <CardDescription className="mb-4 line-clamp-2">
                  {classItem.description}
                </CardDescription>
                
                <div className="space-y-2 text-sm text-gray-600 mb-4">
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-2 text-purple-600" />
                    <span>{classItem.days_of_week.join(", ")}</span>
                  </div>
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-2 text-purple-600" />
                    <span>{classItem.time}</span>
                  </div>
                  <div className="flex items-center">
                    <Users className="h-4 w-4 mr-2 text-purple-600" />
                    <span>{enrollments[classItem.id] || 0} Students</span>
                  </div>
                </div>

                <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => navigate(`/teacher/class/edit/${classItem.id}`)}
                    data-testid={`edit-class-${classItem.id}`}
                  >
                    <Edit className="h-4 w-4 mr-1" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => setDeleteClassId(classItem.id)}
                    data-testid={`delete-class-${classItem.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <AlertDialog open={!!deleteClassId} onOpenChange={() => setDeleteClassId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the class and all related data (students, homework, notices).
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-delete">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => handleDelete(deleteClassId)}
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-delete"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default ClassesOverview;
