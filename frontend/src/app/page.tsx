"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import ConnectButton from "@/components/ConnectButton";

// Shooting Stars Component
const ShootingStars = () => {
    return (
        <div className="fixed inset-0 z-50 overflow-hidden pointer-events-none">
            {[...Array(5)].map((_, i) => (
                <div
                    key={i}
                    className="absolute animate-shooting-star"
                    style={{
                        top: `${Math.random() * 100}%`,
                        left: `${Math.random() * 100}%`,
                        animationDelay: `${Math.random() * 5}s`,
                        animationDuration: `${2 + Math.random() * 3}s`,
                    }}
                >
                    <div className="w-4 h-4 bg-yellow-400 rounded-full shadow-[0_0_10px_2px_rgba(255,255,0,0.8)]" />
                </div>
            ))}
        </div>
    );
};



export default function Home() {
    
    const [style, setStyle] = useState("");
    const [content, setContent] = useState("");
    const [ticker, setTicker] = useState("");
    const [description, setDescription] = useState("");
    const [showVideo, setShowVideo] = useState(false);
    const videoRef = useRef<HTMLVideoElement>(null);

    const handleClick = () => {
        setShowVideo(true);
        setTimeout(() => {
            videoRef.current?.play();
        }, 100); // slight delay to ensure video is rendered
    };

    const handleVideoEnd = () => {
        setShowVideo(false);
        videoRef.current?.pause();
        videoRef.current!.currentTime = 0;
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black text-white p-8 relative">
            <ShootingStars />
            <div className="w-full flex justify-center pb-4">
                    <ConnectButton />
                </div>

            {/* Left GIF */}
            <div className="fixed left-4 -translate-y-1/2 hidden top-1/2 xl:block">
                <Image
                    src="/subway-surfer.gif"
                    alt="Spinning brain gif"
                    width={400}
                    height={800}
                    className="rounded-lg opacity-100 hover:opacity-100 transition-opacity"
                />
            </div>

            {/* Right GIF */}
            <div className="fixed right-4 -translate-y-1/2 hidden top-1/2 xl:block">
                <Image
                    src="/subway-surfer.gif"
                    alt="Matrix brain gif"
                    width={400}
                    height={800}
                    className="rounded-lg opacity-100 hover:opacity-100 transition-opacity"
                />
            </div>

      <div className="max-w-4xl mx-auto relative z-10">
        <h1 className="text-4xl font-bold mb-8 text-center text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">
          BrainRotify™ - The AI That Makes Your Brain Rot Faster
        </h1>
        
        <div className="space-y-10">
          <input
            type="text"
            value={style}
            onChange={(e) => setStyle(e.target.value)}
            placeholder="Style (e.g., 'Extremely loud and obnoxious')"
            className="w-full p-4 bg-gray-800 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <input
            type="text"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Content (e.g., 'Random memes and screaming')"
            className="w-full p-4 bg-gray-800 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="Ticker (e.g., 'SIGMA MALE GRINDSET')"
            className="w-full p-4 bg-gray-800 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (e.g., 'This will make your brain cells commit suicide')"
            className="w-full p-4 bg-gray-800 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
         
        </div>

        <button
          className="w-full mt-8 px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-lg text-white font-bold hover:opacity-90 transition-opacity"
          onClick={handleClick}
        >
          Generate Brain Rot Video
        </button>

                {/* Bottom Square GIF */}
                <div className="flex justify-between">
                    <button
                        className="mt-8 flex justify-start"
                        onClick={handleClick}
                    >
                        <Image
                            src="/button.gif"
                            alt="Exploding brain gif"
                            width={220}
                            height={220}
                            className="rounded-lg opacity-100 hover:opacity-100 transition-opacity"
                        />
                    </button>
                    {showVideo && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90">
                            <video
                                ref={videoRef}
                                src="/0411.mp4"
                                className=" object-cover"
                                onEnded={handleVideoEnd}
                                controls={false}
                                autoPlay
                            />
                        </div>
                    )}
                    <div className="mt-8 flex justify-center p-4">
                        <Image
                            src="/wahoo-fish.gif"
                            alt="Exploding brain gif"
                            width={300}
                            height={300}
                            className="rounded-lg opacity-100 hover:opacity-100 transition-opacity"
                        />
                    </div>
                    <button
                        className="mt-8 flex justify-start"
                        onClick={handleClick}
                    >
                        <Image
                            src="/button.gif"
                            alt="Exploding brain gif"
                            width={220}
                            height={220}
                            className="rounded-lg opacity-100 hover:opacity-100 transition-opacity"
                        />
                    </button>
                    {showVideo && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90">
                            <video
                                ref={videoRef}
                                src="/0411.mp4"
                                className=" object-cover"
                                onEnded={handleVideoEnd}
                                controls={false}
                                autoPlay
                            />
                        </div>
                    )}
                </div>

                <div className="mt-8 text-center text-gray-400 text-sm">
                    <p>
                        Disclaimer: This website is completely unnecessary and
                        exists purely for satirical purposes.
                    </p>
                    <p>
                        No actual brain cells were harmed in the making of this
                        interface.
                    </p>
                </div>
            </div>

            <style jsx global>{`
                @keyframes shooting-star {
                    0% {
                        transform: translateX(-100vw) translateY(-100vh)
                            rotate(45deg);
                        opacity: 0;
                    }
                    50% {
                        opacity: 1;
                    }
                    100% {
                        transform: translateX(100vw) translateY(100vh)
                            rotate(45deg);
                        opacity: 0;
                    }
                }
                .animate-shooting-star {
                    animation: shooting-star linear infinite;
                }
            `}</style>
        </div>
    );
}
