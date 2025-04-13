# Brain Rot AI PumpFun (Brainrotify)

Submission for Encode AI Hackathon

## Features / Todo

- [ ] frontend like full of brainrot to create video and mint
- [ ] backend to generate videos given topic and style with captions

## User Flow

1. User type initial content for reel to be about - Chernobyl, Turtles, Anything really.
2. User select brainrot style - Lobotomy Kaisen, Minecraft Parkour, Soap Cutting, Subway Surfers.
3. Send API Request.
4. Script is generated from initial content. Should be 1 Minute in Length.
5. Script is fed to TTS.
6. Image is generated based on clips.
7. Add subtitles in video.
8. Video is created by splicing Image, Voice and Subtitles. Combining until script is done.
9. Upload Video to IPFS
10. Create metadata and upload to IPFS
11. Return Metadata IPFS Uri back to Frontend.
12. Frontend calls createCoin function of Zora Coin.
