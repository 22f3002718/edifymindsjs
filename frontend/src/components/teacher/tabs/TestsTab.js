import { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Plus, Trash2, FileQuestion, Clock, Users } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import CreateTestDialog from "./CreateTestDialog";
import TestSubmissionsDialog from "./TestSubmissionsDialog";

const TestsTab = ({ classId }) => {
  const [tests, setTests] = useState([]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedTest, setSelectedTest] = useState(null);
  const [submissionsOpen, setSubmissionsOpen] = useState(false);

  useEffect(() => {
    fetchTests();
  }, [classId]);

  const fetchTests = async () => {
    try {
      const response = await axios.get(`${API}/classes/${classId}/tests`);
      setTests(response.data);
    } catch (error) {
      toast.error("Failed to load tests");
    }
  };

  const handleDelete = async (testId) => {
    try {
      await axios.delete(`${API}/tests/${testId}`);
      toast.success("Test deleted successfully");
      setTests(tests.filter(t => t.id !== testId));
    } catch (error) {
      toast.error("Failed to delete test");
    }
  };

  const handleViewSubmissions = (test) => {
    setSelectedTest(test);
    setSubmissionsOpen(true);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-2xl font-semibold">Tests & Assessments</h3>
        <Button 
          className="text-white"
          style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
          onClick={() => setCreateDialogOpen(true)}
          data-testid="create-test-button"
        >
          <Plus className="mr-2 h-4 w-4" />
          Create Test
        </Button>
      </div>

      {tests.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-gray-400">
            <FileQuestion className="h-16 w-16 mx-auto mb-4" />
            <p>No tests created yet</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {tests.map((test) => (
            <Card key={test.id} data-testid={`test-card-${test.id}`}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-xl mb-2">{test.title}</CardTitle>
                    <p className="text-gray-600 mb-3">{test.description}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <div className="flex items-center">
                        <FileQuestion className="h-4 w-4 mr-1" />
                        <span>{test.questions.length} Questions</span>
                      </div>
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        <span>{test.duration_minutes} Minutes</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleViewSubmissions(test)}
                      data-testid={`view-submissions-${test.id}`}
                    >
                      <Users className="h-4 w-4 mr-1" />
                      Submissions
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDelete(test.id)}
                      data-testid={`delete-test-${test.id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      <CreateTestDialog 
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        classId={classId}
        onSuccess={() => {
          fetchTests();
          setCreateDialogOpen(false);
        }}
      />

      {selectedTest && (
        <TestSubmissionsDialog
          open={submissionsOpen}
          onOpenChange={setSubmissionsOpen}
          test={selectedTest}
        />
      )}
    </div>
  );
};

export default TestsTab;
