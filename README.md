# Brain Rot AI PumpFun (Brainrotify)

Generate unique and fun **Brainrot** videos for Zora using your custom parameters!

Submission for Encode AI Hackathon.
2nd Place for Zora Creator Track

## Demo Link

[youtube](https://www.youtube.com/watch?v=UuxnBU78YXM)

## Features

- Content and style inputs to generate desired content.
- Image generation based on the inputs.
- Full script generated for text to speech to nararte.
- Accurate caption timings for the generated **Brainrot** video.
- Uploads content directly to Zora.

## Todo

- [x] frontend like full of brainrot to create video and mint
- [x] backend to generate videos given topic and style with captions

## Flowchart

![Image](https://github.com/user-attachments/assets/96560266-c1cc-475c-abc0-7e6cc63f3325)

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

## Available scripts (Frontend)

### To run the project

```bash
npm run dev
```

### To build the project

```bash
npm run build
```

### To preview the build

```bash
npm run preview
```

### To lint check your code using eslint

```bash
npm run lint
```

### To lint check and fix your code

```bash
npm run lint-fix
```
