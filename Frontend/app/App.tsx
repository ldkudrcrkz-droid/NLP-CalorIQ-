import { useState } from 'react';
import { LandingPage } from './components/LandingPage';
import { ProfileSetup, UserProfile } from './components/ProfileSetup';
import { ChatInterface } from './components/ChatInterface';

type AppState = 'landing' | 'profile' | 'chat';

export default function App() {
  const [state, setState] = useState<AppState>('landing');
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  const handleProfileComplete = (profile: UserProfile) => {
    setUserProfile(profile);
    setState('chat');
  };

  return (
    <div className="size-full">
      {state === 'landing' && (
        <LandingPage onGetStarted={() => setState('profile')} />
      )}
      {state === 'profile' && (
        <ProfileSetup onComplete={handleProfileComplete} />
      )}
      {state === 'chat' && userProfile && (
        <ChatInterface
          userProfile={userProfile}
          onUpdateProfile={() => setState('profile')}
        />
      )}
    </div>
  );
}