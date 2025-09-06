# Music Audio Processor - Project Objectives

## Main Objectives

- [x] **Audio Processing Module** - Create GUI for MP3 file alignment and mixing

  - Drag and drop interface for 3 audio files (original, instrumental, vocal)
  - Cross-correlation audio alignment algorithm
  - Audio mixing with gain control
  - Progress tracking and error handling

- [x] **Music Analysis Module** - Analyze audio characteristics

  - Tempo detection and beat tracking
  - Energy and valence analysis
  - Music section segmentation (intro, verse, chorus, outro)
  - Key detection
  - Simplified JSON output optimized for local LLM processing

- [x] **LLM Integration Module** - AI-powered content generation

  - Local LLM interface (LMStudio with Qwen thinking model)
  - Generate intelligent image search queries based on music analysis
  - JSON-based query format with thinking tag handling
  - Automatic image processing for video compatibility
  - Image curation and selection

- [x] **Video Generation Module** - Automated video creation

  - Sync images with music sections using FFmpeg
  - Smooth crossfade transitions between images
  - Video rendering and export (MP4 format)
  - Multiple output resolutions (1080p, 720p, 4K)
  - Input validation and progress tracking
  - Automatic cleanup after processing

- [ ] **Main Orchestrator** - Complete pipeline integration
  - preserve the music quality as best as possible
  - make sure previously temporary solution like image not downloaded live be reverted back to its working code. and check all temporary solutions. we are trying to make live version.
  - Coordinate all modules
  - User-friendly workflow
  - Error recovery and logging
  - set the final video to 1080p 30fps
  - Remove all tabs
  - Make it into one single page that will process all
  - the final app should only require the three audio file (with its own drop zone, make it compact), with a single button push it should handle every step in the pipeline and output the video.
  - make all looks nice following a good ui ux practice
  - for color follow 60 30 10 rule. keep the main color blue. and the rest black
  - do not display any python terminal, we only need the gui

## Development Notes

- **Clean Code Practice**: Delete all test files after the tested component or function is confirmed to be correct
- **Always Test Before Completion**: When you think a component is done, always test it yourself by running it to ensure it's working properly. Fix any errors immediately.
- **Incremental Development**: Complete and test each module independently before integration
- **User Experience**: Maintain simple, intuitive interfaces with clear progress feedback
