import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Trash2, UserPlus } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const StudentsTab = ({ classId }) => {
  const [students, setStudents] = useState([]);
  const [allStudents, setAllStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchStudents();
    fetchAllStudents();
  }, [classId]);

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${API}/classes/${classId}/students`);
      setStudents(response.data);
    } catch (error) {
      toast.error("Failed to load students");
    }
  };

  const fetchAllStudents = async () => {
    try {
      const response = await axios.get(`${API}/students`);
      setAllStudents(response.data);
    } catch (error) {
      console.error("Failed to load all students");
    }
  };

  const handleAddStudent = async () => {
    if (!selectedStudent) {
      toast.error("Please select a student");
      return;
    }

    try {
      await axios.post(`${API}/enrollments`, {
        student_id: selectedStudent,
        class_id: classId
      });
      toast.success("Student added successfully");
      fetchStudents();
      setSelectedStudent("");
      setDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to add student");
    }
  };

  const handleRemoveStudent = async (studentId) => {
    try {
      await axios.delete(`${API}/enrollments/${studentId}/${classId}`);
      toast.success("Student removed successfully");
      setStudents(students.filter(s => s.id !== studentId));
    } catch (error) {
      toast.error("Failed to remove student");
    }
  };

  const availableStudents = allStudents.filter(
    s => !students.some(enrolled => enrolled.id === s.id)
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-2xl font-semibold">Enrolled Students</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button 
              className="text-white"
              style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
              data-testid="add-student-button"
            >
              <UserPlus className="mr-2 h-4 w-4" />
              Add Student
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Student to Class</DialogTitle>
              <DialogDescription>
                Select a student to enroll in this class
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Select Student</Label>
                <Select value={selectedStudent} onValueChange={setSelectedStudent}>
                  <SelectTrigger data-testid="student-select">
                    <SelectValue placeholder="Choose a student" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableStudents.map((student) => (
                      <SelectItem key={student.id} value={student.id}>
                        {student.name} ({student.email})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button 
                onClick={handleAddStudent}
                className="w-full text-white"
                style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                data-testid="confirm-add-student"
              >
                Add Student
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {students.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-gray-400">
            <UserPlus className="h-16 w-16 mx-auto mb-4" />
            <p>No students enrolled yet</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {students.map((student) => (
            <Card key={student.id} data-testid={`student-card-${student.id}`}>
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{student.name}</CardTitle>
                    <p className="text-sm text-gray-500">{student.email}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => handleRemoveStudent(student.id)}
                    data-testid={`remove-student-${student.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              {student.parent_contact && (
                <CardContent>
                  <p className="text-sm text-gray-600">
                    Parent: {student.parent_contact}
                  </p>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default StudentsTab;
