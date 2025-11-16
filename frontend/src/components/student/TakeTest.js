import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../../App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, Clock, AlertCircle, CheckCircle } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const TakeTest = () => {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchTest();
  }, [testId]);

  useEffect(() => {
    if (timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          // Time's up - auto submit
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  const fetchTest = async () => {
    try {
      const response = await axios.get(`${API}/tests/${testId}`);
      setTest(response.data);
      setTimeLeft(response.data.duration_minutes * 60); // Convert to seconds
    } catch (error) {
      toast.error("Failed to load test");
      navigate(-1);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSubmit = async () => {
    if (submitting) return;
    toast.info("Time's up! Auto-submitting your test...");
    await submitTest();
  };

  const submitTest = async () => {
    setSubmitting(true);
    try {
      // Convert answers object to array format
      const answersArray = Object.entries(answers).map(([index, answer]) => ({
        question_index: parseInt(index),
        selected_answer: answer
      }));

      await axios.post(`${API}/tests/submit`, {
        test_id: testId,
        answers: answersArray
      });

      toast.success("Test submitted successfully!");
      navigate(`/student/test/${testId}/result`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit test");
      setSubmitting(false);
    }
  };

  const handleSubmitClick = () => {
    setSubmitDialogOpen(true);
  };

  const handleConfirmSubmit = () => {
    setSubmitDialogOpen(false);
    submitTest();
  };

  const handleAnswerChange = (value) => {
    setAnswers({
      ...answers,
      [currentQuestionIndex]: value
    });
  };

  const handleNext = () => {
    if (currentQuestionIndex < test.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const answeredCount = Object.keys(answers).length;
  const totalQuestions = test?.questions.length || 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-purple-600 text-xl">Loading test...</div>
      </div>
    );
  }

  if (!test) {
    return <div className="text-center py-12">Test not found</div>;
  }

  const currentQuestion = test.questions[currentQuestionIndex];
  const options = ['A', 'B', 'C', 'D', 'E', 'F'];

  return (
    <div className="animate-fadeIn">
      <Button 
        variant="ghost" 
        onClick={() => navigate(-1)}
        className="mb-6"
        data-testid="back-button"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back
      </Button>

      {/* Header with Timer */}
      <Card className="mb-6" style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}>
        <CardHeader>
          <div className="flex justify-between items-center text-white">
            <div>
              <h1 className="text-3xl font-bold mb-1">{test.title}</h1>
              <p className="text-purple-100">{test.description}</p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-6 w-6" />
                <span className={`text-3xl font-bold ${
                  timeLeft < 60 ? 'text-red-300 animate-pulse' : ''
                }`} data-testid="timer">
                  {formatTime(timeLeft)}
                </span>
              </div>
              <Badge className="bg-white text-purple-700">
                {answeredCount}/{totalQuestions} Answered
              </Badge>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Question Card */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex justify-between items-center mb-2">
            <Badge 
              className="text-white"
              style={{ background: 'linear-gradient(135deg, #9333ea 0%, #c084fc 100%)' }}
            >
              Question {currentQuestionIndex + 1} of {totalQuestions}
            </Badge>
            {answers[currentQuestionIndex] && (
              <Badge className="bg-green-100 text-green-700">
                <CheckCircle className="h-3 w-3 mr-1" />
                Answered
              </Badge>
            )}
          </div>
          <CardTitle className="text-2xl">{currentQuestion.question}</CardTitle>
        </CardHeader>
        <CardContent>
          <RadioGroup 
            value={answers[currentQuestionIndex] || ""} 
            onValueChange={handleAnswerChange}
            data-testid="answer-options"
          >
            <div className="space-y-3">
              {currentQuestion.options.map((option, idx) => (
                <div 
                  key={idx} 
                  className="flex items-center space-x-3 border rounded-lg p-4 hover:bg-purple-50 cursor-pointer"
                  onClick={() => handleAnswerChange(options[idx])}
                >
                  <RadioGroupItem value={options[idx]} id={`option-${idx}`} />
                  <Label 
                    htmlFor={`option-${idx}`} 
                    className="flex-1 cursor-pointer text-lg"
                  >
                    <span className="font-semibold mr-2">{options[idx]})</span>
                    {option}
                  </Label>
                </div>
              ))}
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <Button
          variant="outline"
          onClick={handlePrevious}
          disabled={currentQuestionIndex === 0}
          data-testid="previous-button"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Previous
        </Button>

        <div className="flex gap-2">
          {currentQuestionIndex < totalQuestions - 1 ? (
            <Button
              onClick={handleNext}
              className="text-white"
              style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
              data-testid="next-button"
            >
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmitClick}
              className="text-white font-bold"
              style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
              data-testid="submit-test-button"
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Test"}
            </Button>
          )}
        </div>
      </div>

      {/* Submit Confirmation Dialog */}
      <AlertDialog open={submitDialogOpen} onOpenChange={setSubmitDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Submit Test?</AlertDialogTitle>
            <AlertDialogDescription>
              <div className="space-y-2">
                <p>Are you sure you want to submit your test?</p>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-semibold text-yellow-800">Progress Summary:</p>
                      <p className="text-yellow-700">
                        Answered: {answeredCount}/{totalQuestions} questions
                      </p>
                      {answeredCount < totalQuestions && (
                        <p className="text-yellow-700 mt-1">
                          You have {totalQuestions - answeredCount} unanswered question(s).
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="cancel-submit">Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmSubmit}
              className="bg-green-600 hover:bg-green-700"
              data-testid="confirm-submit"
            >
              Submit Test
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default TakeTest;
