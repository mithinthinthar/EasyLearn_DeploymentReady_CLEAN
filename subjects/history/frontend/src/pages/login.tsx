import React from 'react';
import { useAuth } from '../context/AuthContext';
// import { Navigate } from 'react-router-dom'; // Assuming you might use React Router later, but for now we stick to simple state
import { BookOpen } from 'lucide-react';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const { user, signInWithGoogle } = useAuth();

  if (user) {
      onLoginSuccess();
      return null; // Or a redirect if using router
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <div className="bg-white p-10 rounded-3xl shadow-xl text-center max-w-sm w-full border border-slate-100">
        <div className="bg-indigo-600 text-white p-3 rounded-2xl inline-block mb-6">
          <BookOpen size={32} />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Welcome to EasyLearn</h1>
        <p className="text-slate-500 mb-8">Sign in to start your learning journey.</p>
        
        <button
          onClick={signInWithGoogle}
          className="w-full flex items-center justify-center gap-3 px-6 py-3 border-2 border-slate-200 rounded-xl font-bold text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition"
        >
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="w-6 h-6" />
          Sign in with Google
        </button>
      </div>
    </div>
  );
};

export default Login;