import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Trash2, FileText, Link as LinkIcon, Calendar } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { format } from "date-fns";

const HomeworkTab = ({ classId }) => {
  const [homework, setHomework] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    due_date: "",
    attachment_link: ""
  });

  useEffect(() => {
    fetchHomework();
  }, [classId]);

  const fetchHomework = async () => {
    try {
      const response = await axios.get(`${API}/classes/${classId}/homework`);
      setHomework(response.data);
    } catch (error) {
      toast.error("Failed to load homework");
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/homework`, {
        ...formData,
        class_id: classId
      });
      toast.success("Homework created successfully");
      fetchHomework();
      setFormData({ title: "", description: "", due_date: "", attachment_link: "" });
      setDialogOpen(false);
    } catch (error) {
      toast.error("Failed to create homework");
    }
  };

  const handleDelete = async (homeworkId) => {
    try {
      await axios.delete(`${API}/homework/${homeworkId}`);
      toast.success("Homework deleted successfully");
      setHomework(homework.filter(h => h.id !== homeworkId));
    } catch (error) {
      toast.error("Failed to delete homework");
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-2xl font-semibold">Homework Assignments</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button 
              className="text-white"
              style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
              data-testid="create-homework-button"
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Homework
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Homework</DialogTitle>
              <DialogDescription>
                Add homework assignment for your students
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="hw-title">Title *</Label>
                <Input
                  id="hw-title"
                  data-testid="homework-title-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  placeholder="e.g., Chapter 5 Exercises"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hw-description">Description *</Label>
                <Textarea
                  id="hw-description"
                  data-testid="homework-description-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  rows={4}
                  placeholder="Describe the homework assignment..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hw-due-date">Due Date *</Label>
                <Input
                  id="hw-due-date"
                  data-testid="homework-due-date-input"
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hw-link">Attachment Link (Optional)</Label>
                <Input
                  id="hw-link"
                  data-testid="homework-link-input"
                  value={formData.attachment_link}
                  onChange={(e) => setFormData({ ...formData, attachment_link: e.target.value })}
                  placeholder="Google Drive link or other resource"
                />
              </div>
              <Button 
                type="submit"
                className="w-full text-white"
                style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                data-testid="submit-homework"
              >
                Create Homework
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {homework.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-gray-400">
            <FileText className="h-16 w-16 mx-auto mb-4" />
            <p>No homework assigned yet</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {homework.map((hw) => (
            <Card key={hw.id} data-testid={`homework-card-${hw.id}`}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-xl mb-2">{hw.title}</CardTitle>
                    <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                      <Calendar className="h-4 w-4" />
                      <span>Due: {hw.due_date}</span>
                    </div>
                    <p className="text-gray-600 mt-2">{hw.description}</p>
                    {hw.attachment_link && (
                      <a 
                        href={hw.attachment_link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-purple-600 hover:text-purple-700 mt-2 text-sm"
                        data-testid={`homework-link-${hw.id}`}
                      >
                        <LinkIcon className="h-4 w-4 mr-1" />
                        View Attachment
                      </a>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => handleDelete(hw.id)}
                    data-testid={`delete-homework-${hw.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default HomeworkTab;
