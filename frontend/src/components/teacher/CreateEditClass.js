import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { ArrowLeft, Save } from "lucide-react";

const daysOfWeek = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const CreateEditClass = () => {
  const navigate = useNavigate();
  const { classId } = useParams();
  const isEdit = !!classId;

  const [formData, setFormData] = useState({
    name: "",
    description: "",
    grade_level: "",
    days_of_week: [],
    time: "",
    start_date: "",
    end_date: "",
    zoom_link: "",
    drive_folder_id: ""
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isEdit) {
      fetchClass();
    }
  }, [classId]);

  const fetchClass = async () => {
    try {
      const response = await axios.get(`${API}/classes/${classId}`);
      setFormData(response.data);
    } catch (error) {
      toast.error("Failed to load class");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.days_of_week.length === 0) {
      toast.error("Please select at least one day");
      return;
    }

    setLoading(true);
    try {
      if (isEdit) {
        await axios.put(`${API}/classes/${classId}`, formData);
        toast.success("Class updated successfully");
      } else {
        await axios.post(`${API}/classes`, formData);
        toast.success("Class created successfully");
      }
      navigate('/teacher/classes');
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to save class");
    } finally {
      setLoading(false);
    }
  };

  const handleDayToggle = (day) => {
    setFormData(prev => ({
      ...prev,
      days_of_week: prev.days_of_week.includes(day)
        ? prev.days_of_week.filter(d => d !== day)
        : [...prev.days_of_week, day]
    }));
  };

  return (
    <div className="p-8 max-w-4xl mx-auto animate-fadeIn">
      <Button 
        variant="ghost" 
        onClick={() => navigate('/teacher/classes')}
        className="mb-6"
        data-testid="back-button"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Classes
      </Button>

      <Card>
        <CardHeader>
          <CardTitle className="text-3xl gradient-text" style={{ fontFamily: 'Poppins, sans-serif' }}>
            {isEdit ? 'Edit Class' : 'Create New Class'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="name">Class Name *</Label>
                <Input
                  id="name"
                  data-testid="class-name-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="e.g., Mathematics Grade 5"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="grade_level">Grade/Level *</Label>
                <Input
                  id="grade_level"
                  data-testid="grade-level-input"
                  value={formData.grade_level}
                  onChange={(e) => setFormData({ ...formData, grade_level: e.target.value })}
                  required
                  placeholder="e.g., Grade 5"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                data-testid="description-input"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                required
                rows={4}
                placeholder="Describe what students will learn in this class..."
              />
            </div>

            <div className="space-y-2">
              <Label>Days of Week *</Label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {daysOfWeek.map((day) => (
                  <div key={day} className="flex items-center space-x-2">
                    <Checkbox
                      id={day}
                      data-testid={`day-${day.toLowerCase()}`}
                      checked={formData.days_of_week.includes(day)}
                      onCheckedChange={() => handleDayToggle(day)}
                    />
                    <label htmlFor={day} className="text-sm cursor-pointer">
                      {day}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <Label htmlFor="time">Class Time *</Label>
                <Input
                  id="time"
                  data-testid="time-input"
                  value={formData.time}
                  onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                  required
                  placeholder="e.g., 10:00 AM"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date *</Label>
                <Input
                  id="start_date"
                  data-testid="start-date-input"
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="end_date">End Date (Optional)</Label>
                <Input
                  id="end_date"
                  data-testid="end-date-input"
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="zoom_link">Zoom Live Class Link (Optional)</Label>
              <Input
                id="zoom_link"
                data-testid="zoom-link-input"
                value={formData.zoom_link}
                onChange={(e) => setFormData({ ...formData, zoom_link: e.target.value })}
                placeholder="https://zoom.us/j/..."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="drive_folder_id">Google Drive Folder ID (Optional)</Label>
              <Input
                id="drive_folder_id"
                data-testid="drive-folder-input"
                value={formData.drive_folder_id}
                onChange={(e) => setFormData({ ...formData, drive_folder_id: e.target.value })}
                placeholder="Drive folder ID for resources"
              />
              <p className="text-xs text-gray-500">Get the ID from your Drive folder URL</p>
            </div>

            <div className="flex gap-4">
              <Button
                type="submit"
                data-testid="save-class-button"
                className="text-white font-semibold"
                style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                disabled={loading}
              >
                <Save className="mr-2 h-4 w-4" />
                {loading ? 'Saving...' : (isEdit ? 'Update Class' : 'Create Class')}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/teacher/classes')}
                data-testid="cancel-button"
              >
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default CreateEditClass;
