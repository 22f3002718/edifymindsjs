import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Trash2, FolderOpen, FileText, ExternalLink } from "lucide-react";
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

const ResourcesTab = ({ classId }) => {
  const [resources, setResources] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    type: "file",
    drive_link: ""
  });

  useEffect(() => {
    fetchResources();
  }, [classId]);

  const fetchResources = async () => {
    try {
      const response = await axios.get(`${API}/classes/${classId}/resources`);
      setResources(response.data);
    } catch (error) {
      toast.error("Failed to load resources");
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/resources`, {
        ...formData,
        class_id: classId
      });
      toast.success("Resource added successfully");
      fetchResources();
      setFormData({ name: "", type: "file", drive_link: "" });
      setDialogOpen(false);
    } catch (error) {
      toast.error("Failed to add resource");
    }
  };

  const handleDelete = async (resourceId) => {
    try {
      await axios.delete(`${API}/resources/${resourceId}`);
      toast.success("Resource deleted successfully");
      setResources(resources.filter(r => r.id !== resourceId));
    } catch (error) {
      toast.error("Failed to delete resource");
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-2xl font-semibold">Learning Resources</h3>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button
              className="text-white"
              style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
              data-testid="add-resource-button"
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Resource
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Learning Resource</DialogTitle>
              <DialogDescription>
                Add Google Drive files or folders for students
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="resource-name">Resource Name *</Label>
                <Input
                  id="resource-name"
                  data-testid="resource-name-input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="e.g., Chapter 5 Notes"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="resource-type">Type *</Label>
                <Select value={formData.type} onValueChange={(value) => setFormData({ ...formData, type: value })}>
                  <SelectTrigger data-testid="resource-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="file">File</SelectItem>
                    <SelectItem value="folder">Folder</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="resource-link">Google Drive Link *</Label>
                <Input
                  id="resource-link"
                  data-testid="resource-link-input"
                  value={formData.drive_link}
                  onChange={(e) => setFormData({ ...formData, drive_link: e.target.value })}
                  required
                  placeholder="https://drive.google.com/..."
                />
              </div>
              <Button
                type="submit"
                className="w-full text-white"
                style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                data-testid="submit-resource"
              >
                Add Resource
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {resources.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-gray-400">
            <FolderOpen className="h-16 w-16 mx-auto mb-4" />
            <p>No resources added yet</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {resources.map((resource) => (
            <Card key={resource.id} className="card-hover" data-testid={`resource-card-${resource.id}`}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3 flex-1">
                    {resource.type === "folder" ? (
                      <FolderOpen className="h-8 w-8 text-purple-600 flex-shrink-0" />
                    ) : (
                      <FileText className="h-8 w-8 text-purple-600 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-lg mb-1 break-words">{resource.name}</CardTitle>
                      <Badge variant="secondary" className="text-xs">
                        {resource.type}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 flex-shrink-0"
                    onClick={() => handleDelete(resource.id)}
                    data-testid={`delete-resource-${resource.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <a
                  href={resource.drive_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-purple-600 hover:text-purple-700 text-sm font-medium"
                  data-testid={`open-resource-${resource.id}`}
                >
                  <ExternalLink className="h-4 w-4 mr-1" />
                  Open in Drive
                </a>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ResourcesTab;
