# Circular Visualizer Implementation Guide

## Final Working Solution

After extensive testing, the working circular visualizer uses these exact settings:

### 1. Visualizer Creation Parameters
```python
# Step 1: Create waveform with pure white color
filter = 'showwaves=mode=line:s=1080x1080:colors=0xFFFFFF[v]'
```

### 2. Circular Transformation
```python
# Step 2: Apply circular transformation using geq filter
circular_filter = "geq='p(mod((2*W/(2*PI))*(PI+atan2(0.5*H-Y,X-W/2)),W), H-2*hypot(0.5*H-Y,X-W/2))'"
```

### 3. Overlay Method
```python
# Step 3: Overlay on background with colorkey to remove black
overlay_filter = '[1:v]colorkey=Black:0.1:0.1[ck];[0:v][ck]overlay=(W-w)/2:(H-h)/2[outv]'
```

## Complete Implementation for main_orchestrator.py

### Update the generate_circular_visualizer_video method:

```python
def generate_circular_visualizer_video(self, audio_file):
    """Generate video with background.png and circular white visualizer"""
    
    try:
        self.update_status("Getting audio duration...")
        
        # Step 1: Get audio duration using ffprobe
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 
            'format=duration', '-of', 'csv=p=0', audio_file
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise Exception(f"ffprobe failed: {result.stderr}")
        
        duration = float(result.stdout.strip())
        self.update_status(f"Audio duration: {duration:.2f} seconds")
        
        # Step 2: Create basic background video
        basic_video = "basic_video.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', 'background.png',
            '-i', audio_file,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            '-s', '1920x1080',
            basic_video
        ]
        self._run_ffmpeg_with_progress(cmd, duration, "Creating basic video with background")
        
        # Step 3: Create white waveform visualization (1080x1080, pure white)
        viz_video = "song_viz.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', audio_file,
            '-filter_complex', 
            'showwaves=mode=line:s=1080x1080:colors=0xFFFFFF[v]',
            '-map', '[v]',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            viz_video
        ]
        self._run_ffmpeg_with_progress(cmd, duration, "Creating white waveform visualization")
        
        # Step 4: Create circular visualization
        circle_viz = "song_viz_circle.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', viz_video,
            '-filter_complex',
            "geq='p(mod((2*W/(2*PI))*(PI+atan2(0.5*H-Y,X-W/2)),W), H-2*hypot(0.5*H-Y,X-W/2))'",
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            circle_viz
        ]
        self._run_ffmpeg_with_progress(cmd, duration, "Creating circular visualization")
        
        # Step 5: Overlay circular visualizer on background video
        final_output = "final_music_video.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', basic_video,
            '-i', circle_viz,
            '-filter_complex',
            '[1:v]colorkey=Black:0.1:0.1[ck];[0:v][ck]overlay=(W-w)/2:(H-h)/2[outv]',
            '-map', '[outv]',
            '-map', '0:a',
            '-pix_fmt', 'yuv420p',
            final_output
        ]
        self._run_ffmpeg_with_progress(cmd, duration, "Combining background with circular visualizer")
        
        # Keep intermediate files for debugging if needed
        self.update_status(f"DEBUG: Created files - {basic_video}, {viz_video}, {circle_viz}")
        
        if os.path.exists(final_output):
            file_size = os.path.getsize(final_output)
            self.update_status(f"DEBUG: Final video size: {file_size} bytes")
        
        self.update_status("Circular visualizer video complete!")
        return final_output
        
    except subprocess.TimeoutExpired:
        raise Exception("FFmpeg command timed out")
    except FileNotFoundError:
        raise Exception("FFmpeg not found. Please install FFmpeg and add it to PATH")
    except Exception as e:
        # Clean up on error
        for temp_file in ['basic_video.mp4', 'song_viz.mp4', 'song_viz_circle.mp4']:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        raise e
```

## Key Technical Details

### Color Settings
- **Use `colors=0xFFFFFF`** for pure white (not `colors=white` which gives grey mix)
- **Size `s=1080x1080`** creates full-height circular visualizer on 1920x1080 background

### Overlay Method
- **`colorkey=Black:0.1:0.1`** removes black background from circular visualizer
- **`overlay=(W-w)/2:(H-h)/2`** centers 1080x1080 circle on 1920x1080 background

### File Dependencies
- Requires `background.png` in root directory
- Uses processed audio file from audio processing step
- Outputs `final_music_video.mp4`

## Testing Notes
- Tested working file: `PURE_WHITE_PURE_WHITE_RGB.mp4`
- Shows white circular visualizer with proper background
- No black box artifacts
- 1080px diameter for good visibility
- Pure white color for maximum contrast

## Clean Up
After implementation, remove all test files:
```bash
rm -f *test*.mp4 *PURE_WHITE*.mp4 *FINAL_*.mp4 bg_*.mp4 wave_*.mp4 circular_*.mp4
```