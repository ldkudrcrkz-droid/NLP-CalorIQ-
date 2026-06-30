import { useState } from 'react';
import { TextField, Button, FormControl, FormLabel, RadioGroup, FormControlLabel, Radio } from '@mui/material';
import { User, Activity } from 'lucide-react';

export interface UserProfile {
  gender: 'male' | 'female';
  weight: number;
  height: number;
  age: number;
  bmi?: number;
  bmr?: number;
}

interface ProfileSetupProps {
  onComplete: (profile: UserProfile) => void;
}

export function ProfileSetup({ onComplete }: ProfileSetupProps) {
  const [profile, setProfile] = useState<UserProfile>({
    gender: 'male',
    weight: 0,
    height: 0,
    age: 0
  });

  const calculateBMI = (weight: number, height: number) => {
    if (weight && height) {
      const heightInMeters = height / 100;
      return Number((weight / (heightInMeters * heightInMeters)).toFixed(1));
    }
    return 0;
  };

  const calculateBMR = (gender: 'male' | 'female', weight: number, height: number, age: number) => {
    if (weight && height && age) {
      if (gender === 'male') {
        return Math.round(88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age));
      } else {
        return Math.round(447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age));
      }
    }
    return 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const bmi = calculateBMI(profile.weight, profile.height);
    const bmr = calculateBMR(profile.gender, profile.weight, profile.height, profile.age);
    onComplete({ ...profile, bmi, bmr });
  };

  const isValid = profile.weight > 0 && profile.height > 0 && profile.age > 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Set Up Your Profile</h2>
              <p className="text-sm text-gray-600">Help us personalize your experience</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <FormControl component="fieldset">
              <FormLabel component="legend" sx={{ color: 'text.primary', fontWeight: 600, mb: 1 }}>
                Gender
              </FormLabel>
              <RadioGroup
                row
                value={profile.gender}
                onChange={(e) => setProfile({ ...profile, gender: e.target.value as 'male' | 'female' })}
              >
                <FormControlLabel value="male" control={<Radio />} label="Male" />
                <FormControlLabel value="female" control={<Radio />} label="Female" />
              </RadioGroup>
            </FormControl>

            <TextField
              fullWidth
              label="Weight (kg)"
              type="number"
              value={profile.weight || ''}
              onChange={(e) => setProfile({ ...profile, weight: Number(e.target.value) })}
              inputProps={{ min: 1, step: 0.1 }}
              required
            />

            <TextField
              fullWidth
              label="Height (cm)"
              type="number"
              value={profile.height || ''}
              onChange={(e) => setProfile({ ...profile, height: Number(e.target.value) })}
              inputProps={{ min: 1 }}
              required
            />

            <TextField
              fullWidth
              label="Age"
              type="number"
              value={profile.age || ''}
              onChange={(e) => setProfile({ ...profile, age: Number(e.target.value) })}
              inputProps={{ min: 1, max: 120 }}
              required
            />

            {profile.weight > 0 && profile.height > 0 && (
              <div className="bg-green-50 rounded-lg p-4 flex items-start gap-3">
                <Activity className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-semibold text-gray-900">Your Health Metrics</p>
                  <p className="text-sm text-gray-700 mt-1">
                    BMI: <span className="font-semibold">{calculateBMI(profile.weight, profile.height)}</span>
                  </p>
                  {profile.age > 0 && (
                    <p className="text-sm text-gray-700">
                      BMR: <span className="font-semibold">{calculateBMR(profile.gender, profile.weight, profile.height, profile.age)} cal/day</span>
                    </p>
                  )}
                </div>
              </div>
            )}

            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={!isValid}
              sx={{
                backgroundColor: '#16a34a',
                '&:hover': { backgroundColor: '#15803d' },
                textTransform: 'none',
                fontSize: '1rem',
                padding: '12px',
                borderRadius: '8px',
                mt: 2
              }}
            >
              Continue to Chat
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
