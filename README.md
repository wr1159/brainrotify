# Brain Rot AI PumpFun (Brainrotify)

Submission for Encode AI Hackathon

## Features / Todo

- [ ] frontend like unicorn website full of brainrot, scroll different videos (coins) and can instantly buy
- [ ] frames for buying and selling
- [ ] backend to generate videos given topic and style (minecraft parkour / soap cutting)

## User Flow

1. User type initial content for reel to be about - Chernobyl, Turtles, Anything really.
2. User select brainrot content - Minecraft Parkour, Soap Cutting, Subway Surfers.
3. Pay Our Address 0.002 ETH and send API Request.
4. Script is generated from initial content. Should be 1 Minute in Length.
5. Script is fed to TTS.
6. Image is generated based on clips.
7. Add subtitles in video.
8. Video is created by splicing Image, Voice and Subtitles. Combining until script is done.
9. Upload Video to IPFS
10. Create metadata and upload to IPFS
11. Return Metadata IPFS Uri back to Frontend.
12. Frontend calls createCoin function of Zora Coin.
13. Display Video and show Contract Address.
