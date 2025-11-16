import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { Plus, Trash2, Bell, AlertCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { format } from "date-fns";

const NoticesTab = ({ classId }) => {
  const [notices, setNotices] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    message: "",
    is_important: false
  });

  useEffect(() => {
    fetchNotices();
  }, [classId]);

  const fetchNotices = async () => {
    try {
      const response = await axios.get(`${API}/classes/${classId}/notices`);
      setNotices(response.data);
    } catch (error) {
      toast.error("Failed to load notices");
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/notices`, {
        ...formData,
        class_id: classId
      });
      toast.success("Notice posted successfully");
      fetchNotices();
      setFormData({ title: "", message: "", is_important: false });
      setDialogOpen(false);
    } catch (error) {
      toast.error("Failed to post notice");
    }
  };

  const handleDelete = async (noticeId) => {
    try {
      await axios.delete(`${API}/notices/${noticeId}`);
      toast.success("Notice deleted successfully");
      setNotices(notices.filter(n => n.id !== noticeId));
    } catch (error) {
      toast.error("Failed to delete notice");
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-2xl font-semibold">Class Notices</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button 
              className="text-white"
              style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
              data-testid="create-notice-button"
            >
              <Plus className="mr-2 h-4 w-4" />
              Post Notice
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Post New Notice</DialogTitle>
              <DialogDescription>
                Create an announcement for your students
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="notice-title">Title *</Label>
                <Input
                  id="notice-title"
                  data-testid="notice-title-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  placeholder="e.g., Class Rescheduled"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="notice-message">Message *</Label>
                <Textarea
                  id="notice-message"
                  data-testid="notice-message-input"
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  required
                  rows={4}
                  placeholder="Write your announcement..."
                />
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="important"
                  data-testid="notice-important-checkbox"
                  checked={formData.is_important}
                  onCheckedChange={(checked) => setFormData({ ...formData, is_important: checked })}
                />
                <label htmlFor="important" className="text-sm cursor-pointer">
                  Mark as important
                </label>
              </div>
              <Button 
                type="submit"
                className="w-full text-white"
                style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                data-testid="submit-notice"
              >
                Post Notice
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {notices.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-gray-400">
            <Bell className="h-16 w-16 mx-auto mb-4" />
            <p>No notices posted yet</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {notices.map((notice) => (
            <Card 
              key={notice.id} 
              className={notice.is_important ? "border-2 border-orange-400" : ""}
              data-testid={`notice-card-${notice.id}`}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle className="text-xl">{notice.title}</CardTitle>
                      {notice.is_important && (
                        <Badge className="bg-orange-500 text-white">
                          <AlertCircle className="h-3 w-3 mr-1" />
                          Important
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mb-3">
                      {new Date(notice.created_at).toLocaleDateString()}
                    </p>
                    <p className="text-gray-700">{notice.message}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    onClick={() => handleDelete(notice.id)}
                    data-testid={`delete-notice-${notice.id}`}
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

export default NoticesTab;
