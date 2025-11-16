import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ArrowLeft, Award, Clock, Calendar, TrendingUp, FileQuestion, Eye } from "lucide-react";

const MyTestResults = () => {
  const navigate = useNavigate();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      const response = await axios.get(`${API}/my-test-results`);
      setResults(response.data);
    } catch (error) {
      toast.error("Failed to load test results");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-purple-600 text-xl">Loading your results...</div>
      </div>
    );
  }

  const getScoreColor = (percentage) => {
    if (percentage >= 70) return "bg-green-600";
    if (percentage >= 40) return "bg-yellow-600";
    return "bg-red-600";
  };

  const getScoreGradient = (percentage) => {
    if (percentage >= 70) return "linear-gradient(135deg, #10b981 0%, #059669 100%)";
    if (percentage >= 40) return "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)";
    return "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)";
  };

  return (
    <div className="animate-fadeIn">
      <Button 
        variant="ghost" 
        onClick={() => navigate('/student/dashboard')}
        className="mb-6"
        data-testid="back-to-home"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Home
      </Button>

      {/* Header */}
      <Card className="mb-8" style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}>
        <CardHeader>
          <div className="text-center text-white">
            <div className="flex justify-center mb-4">
              <div className="bg-white rounded-full p-4">
                <Award className="h-16 w-16 text-purple-600" />
              </div>
            </div>
            <h1 className="text-4xl font-bold mb-2">My Test Results</h1>
            <p className="text-xl text-purple-100">
              Track your performance across all tests
            </p>
          </div>
        </CardHeader>
      </Card>

      {results.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-gray-500">
              <FileQuestion className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <p className="text-xl">No test results yet</p>
              <p className="text-sm mt-2">Your completed tests will appear here</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {results.map((result, idx) => {
            const { submission, test, class_name } = result;
            const percentage = Math.round((submission.score / submission.total_questions) * 100);
            
            return (
              <Card 
                key={idx} 
                className="card-hover border-2"
                data-testid={`test-result-${idx}`}
              >
                <CardHeader>
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="flex-1">
                      <CardTitle className="text-2xl mb-2">{test.title}</CardTitle>
                      <div className="flex flex-wrap gap-2 mb-2">
                        <Badge variant="outline" className="text-purple-700 border-purple-300">
                          {class_name}
                        </Badge>
                        <Badge variant="outline">
                          <Calendar className="h-3 w-3 mr-1" />
                          {new Date(submission.submitted_at).toLocaleDateString()}
                        </Badge>
                        <Badge variant="outline">
                          <Clock className="h-3 w-3 mr-1" />
                          {new Date(submission.submitted_at).toLocaleTimeString()}
                        </Badge>
                      </div>
                      {test.description && (
                        <p className="text-gray-600 text-sm">{test.description}</p>
                      )}
                    </div>
                    <div className="flex flex-col items-center">
                      <div 
                        className="text-white rounded-full w-32 h-32 flex flex-col items-center justify-center"
                        style={{ background: getScoreGradient(percentage) }}
                      >
                        <div className="text-4xl font-bold">{percentage}%</div>
                        <div className="text-sm">Score</div>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {submission.score}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">Correct</div>
                    </div>
                    <div className="text-center p-3 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        {submission.total_questions - submission.score}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">Incorrect</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {submission.total_questions}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">Total Questions</div>
                    </div>
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {test.duration_minutes}m
                      </div>
                      <div className="text-xs text-gray-600 mt-1">Duration</div>
                    </div>
                  </div>
                  
                  <Button
                    onClick={() => navigate(`/student/test/${test.id}/result`)}
                    className="w-full text-white"
                    style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                    data-testid={`view-details-${idx}`}
                  >
                    <Eye className="mr-2 h-4 w-4" />
                    View Detailed Review
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MyTestResults;
