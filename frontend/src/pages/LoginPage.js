import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { API } from "../App";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Mail, Lock, User, Phone } from "lucide-react";

const LoginPage = () => {
  const navigate = useNavigate();
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [registerData, setRegisterData] = useState({
    email: "",
    password: "",
    name: "",
    parent_contact: ""
  });
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, loginData);
      const { access_token, user } = response.data;
      
      localStorage.setItem("token", access_token);
      localStorage.setItem("role", user.role);
      localStorage.setItem("user", JSON.stringify(user));
      
      toast.success("Welcome to EdifyMinds Junior!");
      
      if (user.role === "teacher") {
        navigate("/teacher/dashboard");
      } else if (user.role === "admin") {
        navigate("/admin");
      } else {
        navigate("/student/dashboard");
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/register`, {
        ...registerData,
        role: "student"
      });
      const { access_token, user } = response.data;
      
      localStorage.setItem("token", access_token);
      localStorage.setItem("role", user.role);
      localStorage.setItem("user", JSON.stringify(user));
      
      toast.success("Account created successfully!");
      navigate("/student/dashboard");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{
      background: "linear-gradient(135deg, #7B2CBF 0%, #9333ea 50%, #c084fc 100%)"
    }}>
      <div className="w-full max-w-md animate-fadeIn">
        <div className="text-center mb-8">
          <div className="inline-block bg-white rounded-3xl p-6 mb-4 shadow-2xl">
            <img 
              src="https://customer-assets.emergentagent.com/job_3a510027-31fd-46df-a0d7-d59fcd85c43c/artifacts/gjow1soj_image.png" 
              alt="EdifyMinds Junior" 
              className="w-48 h-auto"
            />
          </div>
          <h1 className="text-4xl font-bold text-white mb-2" style={{ fontFamily: 'Poppins, sans-serif' }}>
            Welcome to EdifyMinds Junior!
          </h1>
          <p className="text-purple-100 text-lg">Learn, Grow, and Shine ✨</p>
        </div>

        <Card className="shadow-2xl border-0">
          <CardHeader>
            <CardTitle className="text-2xl" style={{ color: '#7B2CBF' }}>Get Started</CardTitle>
            <CardDescription>Login or create a new student account</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login" className="w-full">
              <TabsList className="grid w-full grid-cols-2 mb-6">
                <TabsTrigger value="login" data-testid="login-tab">Login</TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab">Register</TabsTrigger>
              </TabsList>
              
              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="login-email"
                        data-testid="login-email-input"
                        type="email"
                        placeholder="your.email@example.com"
                        className="pl-10"
                        value={loginData.email}
                        onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="login-password"
                        data-testid="login-password-input"
                        type="password"
                        placeholder="••••••••"
                        className="pl-10"
                        value={loginData.password}
                        onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    data-testid="login-submit-button"
                    className="w-full text-white font-semibold" 
                    style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                    disabled={loading}
                  >
                    {loading ? "Logging in..." : "Login"}
                  </Button>
                </form>
              </TabsContent>
              
              <TabsContent value="register">
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-name">Student Name</Label>
                    <div className="relative">
                      <User className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="register-name"
                        data-testid="register-name-input"
                        type="text"
                        placeholder="John Doe"
                        className="pl-10"
                        value={registerData.name}
                        onChange={(e) => setRegisterData({ ...registerData, name: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="register-email"
                        data-testid="register-email-input"
                        type="email"
                        placeholder="student@example.com"
                        className="pl-10"
                        value={registerData.email}
                        onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="register-password"
                        data-testid="register-password-input"
                        type="password"
                        placeholder="••••••••"
                        className="pl-10"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-contact">Parent Contact (Optional)</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                      <Input
                        id="register-contact"
                        data-testid="register-contact-input"
                        type="text"
                        placeholder="+1234567890"
                        className="pl-10"
                        value={registerData.parent_contact}
                        onChange={(e) => setRegisterData({ ...registerData, parent_contact: e.target.value })}
                      />
                    </div>
                  </div>
                  <Button 
                    type="submit" 
                    data-testid="register-submit-button"
                    className="w-full text-white font-semibold" 
                    style={{ background: 'linear-gradient(135deg, #7B2CBF 0%, #9333ea 100%)' }}
                    disabled={loading}
                  >
                    {loading ? "Creating Account..." : "Create Account"}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
        
        <p className="text-center text-white text-sm mt-4">
          Teacher Demo: edify@gmail.com / edify123
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
