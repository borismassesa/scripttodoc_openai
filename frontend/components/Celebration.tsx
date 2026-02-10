'use client';

import { useEffect, useState } from 'react';
import { PartyPopper, X } from 'lucide-react';

interface CelebrationProps {
  onClose: () => void;
  documentTitle?: string;
}

export default function Celebration({ onClose, documentTitle }: CelebrationProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    // Trigger animation
    setIsVisible(true);

    // Auto-dismiss after 5 seconds
    const timer = setTimeout(() => {
      handleClose();
    }, 5000);

    return () => clearTimeout(timer);
  }, []);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300); // Wait for fade-out animation
  };

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      onClick={handleClose}
    >
      {/* Confetti Container - Respects reduced motion preferences */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Generate confetti pieces (40 for reduced motion, 150 for full animation) */}
        {!prefersReducedMotion && [...Array(150)].map((_, i) => (
          <div
            key={i}
            className="confetti absolute"
            style={{
              left: `${Math.random() * 100}%`,
              top: `-${Math.random() * 100}px`,
              width: `${Math.random() * 15 + 5}px`,
              height: `${Math.random() * 15 + 5}px`,
              backgroundColor: [
                '#3B82F6', // blue
                '#8B5CF6', // purple
                '#F59E0B', // amber
                '#10B981', // emerald
                '#EF4444', // red
                '#EC4899', // pink
                '#F97316', // orange
                '#14B8A6', // teal
                '#6366F1', // indigo
                '#A855F7', // purple
                '#F43F5E', // rose
                '#FCD34D', // yellow
              ][Math.floor(Math.random() * 12)],
              animationDelay: `${Math.random() * 4}s`,
              animationDuration: `${Math.random() * 4 + 3}s`,
              transform: `rotate(${Math.random() * 360}deg)`,
              opacity: Math.random() * 0.5 + 0.5,
            }}
          />
        ))}

        {/* Sparkle stars for extra magic ✨ (only if motion is not reduced) */}
        {!prefersReducedMotion && [...Array(30)].map((_, i) => (
          <div
            key={`star-${i}`}
            className="absolute text-yellow-300 animate-pulse"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              fontSize: `${Math.random() * 20 + 10}px`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${Math.random() * 2 + 1}s`,
            }}
          >
            ✨
          </div>
        ))}

        {/* Static celebration for reduced motion users */}
        {prefersReducedMotion && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-8xl opacity-20">🎉</div>
          </div>
        )}
      </div>

      {/* Celebration Card */}
      <div
        className={`relative bg-white rounded-2xl shadow-2xl p-8 max-w-md mx-4 transform transition-all duration-500 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-4'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-full hover:bg-gray-100"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Content */}
        <div className="text-center space-y-6">
          {/* Corgi Mascot with Bounce Animation (respects reduced motion) */}
          <div className="relative flex justify-center">
            <div className={`relative ${!prefersReducedMotion ? 'animate-bounce-celebration' : ''}`}>
              <img
                src="/images/corgi-mascot.png"
                alt="Celebrating Corgi"
                className="w-40 h-40 object-contain"
              />
              {/* Party popper icon */}
              <div className={`absolute -top-2 -right-2 ${!prefersReducedMotion ? 'animate-wiggle' : ''}`}>
                <PartyPopper className="w-12 h-12 text-yellow-500" />
              </div>
            </div>
          </div>

          {/* Success Message - ENHANCED! (respects reduced motion) */}
          <div className="space-y-3">
            <h2 className="text-4xl font-extrabold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent flex items-center justify-center gap-2">
              <span className={!prefersReducedMotion ? 'animate-bounce' : ''}>🎉</span>
              <span>Success!</span>
              <span className={!prefersReducedMotion ? 'animate-bounce' : ''} style={{ animationDelay: '0.1s' }}>🎉</span>
            </h2>
            <p className="text-xl text-gray-800 font-bold">
              {documentTitle ? `"${documentTitle}"` : 'Your document'} is ready!
            </p>
            <div className="inline-flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-full font-semibold text-sm">
              <span className="text-2xl">✅</span>
              <span>Processing Complete</span>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              Your document has been successfully generated and is ready to download!
              Check the <span className="font-semibold text-blue-600">History</span> tab to view and download it.
            </p>
          </div>

          {/* Dismiss Button */}
          <button
            onClick={handleClose}
            className="mt-4 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-lg"
          >
            Awesome!
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes confetti-fall {
          0% {
            transform: translateY(-20px) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
          }
        }

        @keyframes bounce-celebration {
          0%, 100% {
            transform: translateY(0) scale(1);
          }
          25% {
            transform: translateY(-20px) scale(1.1);
          }
          50% {
            transform: translateY(0) scale(1);
          }
          75% {
            transform: translateY(-10px) scale(1.05);
          }
        }

        @keyframes wiggle {
          0%, 100% {
            transform: rotate(-12deg);
          }
          50% {
            transform: rotate(12deg);
          }
        }

        .confetti {
          animation: confetti-fall linear forwards;
          border-radius: 50%;
        }

        .animate-bounce-celebration {
          animation: bounce-celebration 1s ease-in-out 2;
        }

        .animate-wiggle {
          animation: wiggle 0.5s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
