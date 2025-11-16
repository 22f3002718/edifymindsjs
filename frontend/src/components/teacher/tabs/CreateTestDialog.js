import { useState } from "react";
import axios from "axios";
import { API } from "../../../App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AlertCircle } from "lucide-react";

const CreateTestDialog = ({ open, onOpenChange, classId, onSuccess }) => {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    duration_minutes: 30,
    questions_text: ""
  });
  const [loading, setLoading] = useState(false);

  const exampleFormat = `Q1. What is 2 + 2?
A) 3
B) 4
C) 5
D) 6
ANSWER: B

Q2. What is the capital of France?
A) London
B) Berlin
C) Paris
D) Madrid
ANSWER: C`;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/tests`, {
        ...formData,
        class_id: classId
      });
      toast.success("Test created successfully");
      setFormData({ title: "", description: "", duration_minutes: 30, questions_text: "" });
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create test");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Test</DialogTitle>
          <DialogDescription>
            Add test details and paste questions in the specified format
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="test-title">Test Title *</Label>
              <Input
                id="test-title"
                data-testid="test-title-input"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
                placeholder="e.g., Math Quiz - Chapter 5"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="test-duration">Duration (minutes) *</Label>
              <Input
                id="test-duration"
                data-testid="test-duration-input"
                type="number"
                min="1"
                value={formData.duration_minutes}
                onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="test-description">Description</Label>
            <Textarea
              id="test-description"
              data-testid="test-description-input"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={2}
              placeholder="Brief description of the test"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="questions-text">Questions (Paste in format below) *</Label>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-2">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-800">
                  <p className="font-semibold mb-1">Format Instructions:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Question line starts with <code className="bg-white px-1 rounded">Q</code></li>
                    <li>Option lines start with <code className="bg-white px-1 rounded">A)</code>, <code className="bg-white px-1 rounded">B)</code>, <code className="bg-white px-1 rounded">C)</code>, etc.</li>
                    <li>Answer line starts with <code className="bg-white px-1 rounded">ANSWER:</code></li>
                    <li>Leave blank line between questions</li>
                  </ul>
                </div>
              </div>
            </div>
            <Textarea
              id="questions-text"
              data-testid="questions-text-input"
              value={formData.questions_text}
              onChange={(e) => setFormData({ ...formData, questions_text: e.target.value })}
              rows={12}
              required
              placeholder={exampleFormat}
              className="font-mono text-sm"
            />
          </div>

          <div className="flex gap-2">
            <Button 
              type="submit"
              className="text-white"
              style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
              disabled={loading}
              data-testid="submit-test"
            >
              {loading ? "Creating..." : "Create Test"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateTestDialog;
