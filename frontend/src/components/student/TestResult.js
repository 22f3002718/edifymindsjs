import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { ArrowLeft, Award, CheckCircle, XCircle, TrendingUp } from "lucide-react";

const TestResult = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResult();
  }, [testId]);

  const fetchResult = async () => {
    try {
      const response = await axios.get(`${API}/tests/${testId}/result`);
      setResult(response.data);
    } catch (error) {
      toast.error("Failed to load test result");
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-purple-600 text-xl">Loading results...</div>
      </div>
    );
  }

  if (!result) {
    return <div className="text-center py-12">Result not found</div>;
  }

  const { submission, test } = result;
  const percentage = Math.round((submission.score / submission.total_questions) * 100);
  const options = ['A', 'B', 'C', 'D', 'E', 'F'];

  // Create a map of student answers
  const studentAnswersMap = {};
  submission.answers.forEach(ans => {
    studentAnswersMap[ans.question_index] = ans.selected_answer;
  });

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

      {/* Score Card */}
      <Card className="mb-8" style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}>
        <CardHeader>
          <div className="text-center text-white">
            <div className="flex justify-center mb-4">
              <div className="bg-white rounded-full p-4">
                <Award className="h-16 w-16 text-purple-600" />
              </div>
            </div>
            <h1 className="text-4xl font-bold mb-2">Test Complete!</h1>
            <p className="text-xl text-purple-100 mb-4">{test.title}</p>
            
            <div className="flex justify-center items-center gap-8 mt-6">
              <div>
                <div className="text-6xl font-bold">{percentage}%</div>
                <div className="text-purple-100 mt-2">Overall Score</div>
              </div>
              <div className="h-16 w-px bg-purple-300" />
              <div>
                <div className="text-5xl font-bold">{submission.score}/{submission.total_questions}</div>
                <div className="text-purple-100 mt-2">Questions Correct</div>
              </div>
            </div>

            <Badge 
              className="mt-6 text-lg px-6 py-2"
              style={{ 
                background: percentage >= 70 
                  ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                  : percentage >= 40
                  ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                  : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
              }}
            >
              {percentage >= 70 ? "Excellent!" : percentage >= 40 ? "Good Effort!" : "Keep Practicing!"}
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Detailed Review */}
      <div className="mb-6">
        <h2 className="text-3xl font-bold gradient-text mb-4">Detailed Review</h2>
        <p className="text-gray-600 mb-6">Review each question with your answer and the correct answer</p>
      </div>

      <div className="space-y-6">
        {test.questions.map((question, idx) => {
          const studentAnswer = studentAnswersMap[idx];
          const isCorrect = studentAnswer?.toUpperCase() === question.correct_answer.toUpperCase();
          
          return (
            <Card 
              key={idx} 
              className={`border-2 ${isCorrect ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}
              data-testid={`question-review-${idx}`}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">Question {idx + 1}</Badge>
                      {isCorrect ? (
                        <Badge className="bg-green-600 text-white">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Correct
                        </Badge>
                      ) : (
                        <Badge className="bg-red-600 text-white">
                          <XCircle className="h-3 w-3 mr-1" />
                          Incorrect
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-xl">{question.question}</CardTitle>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {question.options.map((option, optIdx) => {
                    const optionLetter = options[optIdx];
                    const isStudentAnswer = studentAnswer?.toUpperCase() === optionLetter.toUpperCase();
                    const isCorrectAnswer = question.correct_answer.toUpperCase() === optionLetter.toUpperCase();
                    
                    return (
                      <div 
                        key={optIdx}
                        className={`border rounded-lg p-4 ${
                          isCorrectAnswer 
                            ? 'bg-green-100 border-green-300' 
                            : isStudentAnswer 
                            ? 'bg-red-100 border-red-300' 
                            : 'bg-white'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          <span className="font-semibold">{optionLetter})</span>
                          <span className="flex-1">{option}</span>
                          {isCorrectAnswer && (
                            <Badge className="bg-green-600 text-white">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Correct Answer
                            </Badge>
                          )}
                          {isStudentAnswer && !isCorrectAnswer && (
                            <Badge className="bg-red-600 text-white">
                              Your Answer
                            </Badge>
                          )}
                          {isStudentAnswer && isCorrectAnswer && (
                            <Badge className="bg-green-600 text-white">
                              Your Answer
                            </Badge>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {!studentAnswer && (
                  <div className="mt-4 bg-yellow-100 border border-yellow-300 rounded-lg p-3 text-sm text-yellow-800">
                    You did not answer this question
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Performance Summary */}
      <Card className="mt-8 mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-6 w-6 text-purple-600" />
            Performance Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">
                {submission.score}
              </div>
              <div className="text-sm text-gray-600 mt-1">Correct Answers</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-3xl font-bold text-red-600">
                {submission.total_questions - submission.score}
              </div>
              <div className="text-sm text-gray-600 mt-1">Incorrect Answers</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl font-bold text-purple-600">
                {percentage}%
              </div>
              <div className="text-sm text-gray-600 mt-1">Overall Score</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TestResult;
