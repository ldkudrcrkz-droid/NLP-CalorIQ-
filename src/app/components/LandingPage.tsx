import { ChefHat, Sparkles, Heart, TrendingDown } from 'lucide-react';
import { Button } from '@mui/material';

interface LandingPageProps {
  onGetStarted: () => void;
}

export function LandingPage({ onGetStarted }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      {/* Header */}
      <header className="p-6">
        <div className="flex items-center gap-2">
          <ChefHat className="w-8 h-8 text-green-600" />
          <span className="text-2xl font-bold text-gray-800">CalorIQ</span>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-6 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-green-100 rounded-full mb-8">
            <Sparkles className="w-4 h-4 text-green-600" />
            <span className="text-sm font-medium text-green-700">AI-Powered Nutrition Assistant</span>
          </div>

          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Personalized Recipe Recommendations
            <br />
            <span className="text-green-600">Tailored to Your Health</span>
          </h1>

          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Get intelligent recipe suggestions based on your BMI, nutritional needs, and taste preferences.
            Eat healthy without compromising on flavor.
          </p>

          <Button
            variant="contained"
            size="large"
            onClick={onGetStarted}
            sx={{
              backgroundColor: '#16a34a',
              '&:hover': { backgroundColor: '#15803d' },
              textTransform: 'none',
              fontSize: '1.125rem',
              padding: '12px 48px',
              borderRadius: '8px'
            }}
          >
            Get Started
          </Button>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mt-20">
            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                <Heart className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Personalized Nutrition</h3>
              <p className="text-gray-600 text-sm">
                Recipes matched to your BMI, BMR, and specific nutritional requirements
              </p>
            </div>

            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                <Sparkles className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">AI Chatbot</h3>
              <p className="text-gray-600 text-sm">
                Natural conversation to find exactly what you're craving
              </p>
            </div>

            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4 mx-auto">
                <TrendingDown className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Low-Calorie Focus</h3>
              <p className="text-gray-600 text-sm">
                Smart filtering for calorie-conscious meal planning
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
