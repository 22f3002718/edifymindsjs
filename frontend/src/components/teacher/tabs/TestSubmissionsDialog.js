import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../../../App";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { User, Award, Calendar } from "lucide-react";

const TestSubmissionsDialog = ({ open, onOpenChange, test }) => {
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (open && test) {
      fetchSubmissions();
    }
  }, [open, test]);

  const fetchSubmissions = async () => {
    try {
      const response = await axios.get(`${API}/tests/${test.id}/submissions`);
      setSubmissions(response.data);
    } catch (error) {
      toast.error("Failed to load submissions");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl">Test Submissions - {test?.title}</DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : submissions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No submissions yet
          </div>
        ) : (
          <div className="space-y-3">
            {submissions.map((submission) => (
              <div 
                key={submission.id} 
                className="border rounded-lg p-4 hover:bg-gray-50"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="bg-purple-100 rounded-full p-2">
                      <User className="h-5 w-5 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-lg">{submission.student_name}</h4>
                      <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                        <Calendar className="h-4 w-4" />
                        <span>{new Date(submission.submitted_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-2 mb-1">
                      <Award className="h-5 w-5 text-yellow-500" />
                      <span className="text-2xl font-bold" style={{ color: '#7B2CBF' }}>
                        {submission.score}/{submission.total_questions}
                      </span>
                    </div>
                    <Badge 
                      className="text-white"
                      style={{ 
                        background: submission.score / submission.total_questions >= 0.7 
                          ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                          : submission.score / submission.total_questions >= 0.4
                          ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                          : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                      }}
                    >
                      {Math.round((submission.score / submission.total_questions) * 100)}%
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default TestSubmissionsDialog;
