import React, { useState } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../contexts/AuthContext'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Eye, EyeOff, Mail, Lock, LogIn, UserPlus } from 'lucide-react'

interface LoginForm {
  email: string
  password: string
}

export default function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { signIn, signUp } = useAuth()
  const router = useRouter()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<LoginForm>()

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    try {
      if (isLogin) {
        await signIn(data.email, data.password)
        toast.success('Welcome back!')
        router.push('/dashboard')
      } else {
        await signUp(data.email, data.password)
        toast.success('Account created! Please check your email to verify.')
      }
    } catch (error: any) {
      toast.error(error.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    reset()
  }

  return (
    <div className="min-h-screen animated-bg flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-cyan-500/20 to-green-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-purple-500/20 to-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>
      
      <div className="max-w-lg w-full space-y-8 relative z-10">
        <div className="text-center">
          <div className="mx-auto h-20 w-20 bg-gradient-to-br from-cyan-400 to-green-400 rounded-2xl flex items-center justify-center glow-green status-glow">
            <LogIn className="h-10 w-10 text-black" />
          </div>
          <h2 className="mt-8 text-4xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
            {isLogin ? 'WELCOME BACK' : 'CREATE ACCOUNT'}
          </h2>
          <p className="mt-4 text-lg text-gray-300">
            {isLogin ? 'Sign in to your CareerPilot account' : 'Join CareerPilot to automate your job search'}
          </p>
        </div>

        <form className="mt-8 space-y-8" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-lg font-semibold text-gray-200 mb-3">
                EMAIL ADDRESS
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="h-6 w-6 text-cyan-400" />
                </div>
                <input
                  {...register('email', {
                    required: 'Email is required',
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: 'Invalid email address',
                    },
                  })}
                  type="email"
                  className="input-futuristic block w-full pl-12 pr-4 py-4 text-lg rounded-xl placeholder-gray-500"
                  placeholder="Enter your email"
                />
              </div>
              {errors.email && (
                <p className="mt-2 text-sm text-red-400">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-lg font-semibold text-gray-200 mb-3">
                PASSWORD
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="h-6 w-6 text-cyan-400" />
                </div>
                <input
                  {...register('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters',
                    },
                  })}
                  type={showPassword ? 'text' : 'password'}
                  className="input-futuristic block w-full pl-12 pr-12 py-4 text-lg rounded-xl placeholder-gray-500"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-4 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-6 w-6 text-gray-400 hover:text-cyan-400 transition-colors" />
                  ) : (
                    <Eye className="h-6 w-6 text-gray-400 hover:text-cyan-400 transition-colors" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-2 text-sm text-red-400">{errors.password.message}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="btn-futuristic w-full flex justify-center py-4 px-6 text-lg font-bold rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
              ) : (
                <>
                  {isLogin ? (
                    <>
                      <LogIn className="h-6 w-6 mr-3" />
                      SIGN IN
                    </>
                  ) : (
                    <>
                      <UserPlus className="h-6 w-6 mr-3" />
                      CREATE ACCOUNT
                    </>
                  )}
                </>
              )}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={toggleMode}
              className="text-cyan-400 hover:text-green-400 text-lg font-semibold transition-colors duration-300"
            >
              {isLogin ? "Don't have an account? SIGN UP" : 'Already have an account? SIGN IN'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
