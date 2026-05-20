import { useState, useRef, useEffect } from 'react';
import { TextField, Button, IconButton, Chip, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { Send, Bot, User, ChefHat, Settings, X } from 'lucide-react';
import { RecipeCard, Recipe } from './RecipeCard';
import { UserProfile } from './ProfileSetup';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  recipes?: Recipe[];
}

interface ChatInterfaceProps {
  userProfile: UserProfile;
  onUpdateProfile: () => void;
}

export function ChatInterface({ userProfile, onUpdateProfile }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hi! I'm CalorIQ, your personal nutrition assistant. Based on your profile, your BMI is ${userProfile.bmi} and your daily caloric need (BMR) is around ${userProfile.bmr} calories. What kind of recipe are you looking for today?`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fungsi pengiriman pesan terpadu
  const sendMessage = async (textToSend: string) => {
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          profile: {
            gender: userProfile.gender,
            age: userProfile.age,
            weight: userProfile.weight,
            height: userProfile.height
          },
          query: textToSend
        })
      });

      if (!response.ok) {
        throw new Error('Gagal terhubung dengan server AI.');
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.content,
        recipes: data.recipes
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Maaf, terjadi masalah koneksi atau kegagalan pemrosesan pada model server AI.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    sendMessage(input);
    setInput('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickPrompts = [
    'Low-calorie breakfast',
    'High-protein lunch',
    'Healthy chicken salad',
    'Quick snacks'
  ];

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
            <ChefHat className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h1 className="font-bold text-gray-900">CalorIQ</h1>
            <p className="text-xs text-gray-500">BMI: {userProfile.bmi} | BMR: {userProfile.bmr} cal/day</p>
          </div>
        </div>
        <IconButton onClick={onUpdateProfile} size="small">
          <Settings className="w-5 h-5" />
        </IconButton>
      </header>

      {/* Messages List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-3 max-w-3xl ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'user' ? 'bg-blue-100' : 'bg-green-100'
              }`}>
                {message.role === 'user' ? <User className="w-4 h-4 text-blue-600" /> : <Bot className="w-4 h-4 text-green-600" />}
              </div>
              <div className="flex-1">
                <div className={`rounded-2xl px-4 py-3 ${
                  message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-900'
                }`}>
                  {message.content}
                </div>
                {message.recipes && (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                    {message.recipes.map((recipe) => (
                      <RecipeCard
                        key={recipe.id}
                        recipe={recipe}
                        onClick={() => setSelectedRecipe(recipe)}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-sm text-gray-400 italic pl-11">CalorIQ sedang menganalisis nutrisi...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          {messages.length === 1 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {quickPrompts.map((prompt) => (
                <Chip
                  key={prompt}
                  label={prompt}
                  onClick={() => sendMessage(prompt)}
                  sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                />
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <TextField
              fullWidth
              placeholder="Ask for recipe recommendations..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              variant="outlined"
              size="small"
              disabled={loading}
              sx={{ '& .MuiOutlinedInput-root': { borderRadius: '12px' } }}
            />
            <Button
              variant="contained"
              onClick={handleSend}
              disabled={!input.trim() || loading}
              sx={{
                backgroundColor: '#16a34a',
                '&:hover': { backgroundColor: '#15803d' },
                minWidth: '48px',
                borderRadius: '12px'
              }}
            >
              <Send className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Recipe Detail Dialog */}
      <Dialog open={!!selectedRecipe} onClose={() => setSelectedRecipe(null)} maxWidth="md" fullWidth>
        {selectedRecipe && (
          <>
            <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="font-bold">{selectedRecipe.name}</span>
              <IconButton onClick={() => setSelectedRecipe(null)} size="small" sx={{ ml: 'auto' }}>
                <X className="w-5 h-5" />
              </IconButton>
            </DialogTitle>
            <DialogContent dividers>
              <p className="text-gray-700 mb-4">{selectedRecipe.description}</p>
              <h3 className="font-semibold text-lg mb-2">Nutritional Information</h3>
              <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-orange-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-orange-600">{selectedRecipe.calories}</p>
                  <p className="text-sm text-gray-600">Calories</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-red-600">{selectedRecipe.protein}g</p>
                  <p className="text-sm text-gray-600">Protein</p>
                </div>
                <div className="bg-yellow-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-yellow-600">{selectedRecipe.fat}g</p>
                  <p className="text-sm text-gray-600">Fat</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <p className="text-2xl font-bold text-blue-600">{selectedRecipe.carbs}g</p>
                  <p className="text-sm text-gray-600">Carbs</p>
                </div>
              </div>
              {selectedRecipe.steps && (
                <>
                  <h3 className="font-semibold text-lg mb-2">Instructions</h3>
                  <ol className="list-decimal list-inside space-y-2 text-gray-700">
                    {selectedRecipe.steps.map((step, idx) => (
                      <li key={idx}>{step}</li>
                    ))}
                  </ol>
                </>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedRecipe(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </div>
  );
}