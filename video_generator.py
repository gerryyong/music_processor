import os
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import subprocess
import tempfile
from pathlib import Path

@dataclass
class VideoSection:
    """Represents a video section with timing and image"""
    start_time: float
    end_time: float
    duration: float
    section_type: str
    image_path: str
    transition_type: str = "crossfade"

class VideoGenerator:
    """Generate music videos from processed images and audio analysis"""
    
    def __init__(self, output_resolution: Tuple[int, int] = (1920, 1080), fps: int = 30):
        """
        Initialize video generator
        
        Args:
            output_resolution: Video resolution (width, height)
            fps: Frames per second
        """
        self.width, self.height = output_resolution
        self.fps = fps
        self.check_ffmpeg()
    
    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg not found! Please install FFmpeg:\n"
                "1. Download from https://ffmpeg.org/download.html\n"
                "2. Add to PATH, or\n"
                "3. Install via package manager (e.g., winget install ffmpeg)"
            )
    
    def create_video_from_analysis(self, 
                                 music_analysis: Dict[str, Any],
                                 processed_images_dir: str,
                                 audio_file: str,
                                 output_path: str,
                                 transition_duration: float = 1.0,
                                 progress_callback=None,
                                 add_visualizer: bool = True,
                                 use_fade_transitions: bool = True,
                                 visualizer_style: str = "spectrum_waves") -> str:
        """
        Create video from music analysis and processed images
        
        Args:
            music_analysis: Music analysis JSON
            processed_images_dir: Directory with processed images
            audio_file: Path to audio file
            output_path: Output video path
            transition_duration: Duration of crossfade transitions in seconds
            
        Returns:
            Path to generated video
        """
        # Find processed images for each section
        video_sections = self._prepare_video_sections(music_analysis, processed_images_dir)
        
        if not video_sections:
            raise ValueError("No processed images found for video generation")
        
        # Generate video with new options
        if use_fade_transitions:
            return self._create_video_with_fade_transitions(
                video_sections, audio_file, output_path, 
                transition_duration, progress_callback, add_visualizer, visualizer_style, music_analysis
            )
        else:
            return self._generate_video_ffmpeg(
                video_sections, audio_file, output_path, 
                transition_duration, progress_callback, add_visualizer
            )
    
    def _prepare_video_sections(self, music_analysis: Dict[str, Any], 
                              processed_images_dir: str) -> List[VideoSection]:
        """Prepare video sections from analysis and find corresponding images"""
        
        video_sections = []
        sections = music_analysis.get('video_sections', [])
        
        for i, section in enumerate(sections):
            # Look for processed images for this section
            section_dir = os.path.join(processed_images_dir, f"section_{i}")
            
            if not os.path.exists(section_dir):
                print(f"Warning: No processed images found for section {i}")
                continue
            
            # Find the first processed image in the section
            image_files = [f for f in os.listdir(section_dir) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if not image_files:
                print(f"Warning: No image files found in {section_dir}")
                continue
            
            # Use the first available image
            image_path = os.path.join(section_dir, image_files[0])
            
            # Determine transition type based on energy
            energy = section.get('energy', 0.5)
            if energy > 0.7:
                transition_type = "quick_cut"
            elif energy > 0.4:
                transition_type = "crossfade"
            else:
                transition_type = "slow_fade"
            
            video_section = VideoSection(
                start_time=section.get('start', 0),
                end_time=section.get('end', 0),
                duration=section.get('end', 0) - section.get('start', 0),
                section_type=section.get('type', 'unknown'),
                image_path=image_path,
                transition_type=transition_type
            )
            
            video_sections.append(video_section)
        
        return video_sections
    
    def _generate_video_ffmpeg(self, sections: List[VideoSection], 
                             audio_file: str, output_path: str, 
                             transition_duration: float,
                             progress_callback=None, 
                             add_visualizer: bool = False) -> str:
        """Generate video using FFmpeg with smooth transitions"""
        
        if len(sections) == 1:
            # Simple case: single image for entire video
            return self._create_single_image_video(sections[0], audio_file, output_path, progress_callback)
        
        # Complex case: multiple sections with transitions
        return self._create_multi_section_video(sections, audio_file, output_path, transition_duration)
    
    def _create_single_image_video(self, section: VideoSection, 
                                 audio_file: str, output_path: str,
                                 progress_callback=None) -> str:
        """Create video from single image"""
        
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-loop', '1',
            '-i', section.image_path,  # Input image
            '-i', audio_file,  # Input audio
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-vf', f'scale={self.width}:{self.height}:force_original_aspect_ratio=increase,crop={self.width}:{self.height}',
            '-r', str(self.fps),
            '-shortest',  # End when audio ends
            output_path
        ]
        
        
        # Use Popen for real-time progress if callback provided
        if progress_callback:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True)
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output and 'out_time=' in output:
                    try:
                        time_str = output.split('out_time=')[1].strip()
                        if ':' in time_str:
                            parts = time_str.split(':')
                            current_time = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                            total_time = section.duration if section else 180
                            if total_time > 0:
                                progress_percent = min((current_time / total_time) * 100, 100)
                                progress_callback(f"Rendering video... {current_time:.1f}s/{total_time:.1f}s", int(progress_percent))
                    except:
                        pass
            
            if process.returncode != 0:
                stderr_output = process.stderr.read()
                raise RuntimeError(f"FFmpeg failed: {stderr_output}")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
        return output_path
    
    def _create_multi_section_video(self, sections: List[VideoSection], 
                                  audio_file: str, output_path: str,
                                  transition_duration: float) -> str:
        """Create video with multiple sections using fixed FFmpeg filter"""
        
        print(f"Creating multi-section video with {len(sections)} sections")
        
        # Build inputs: audio first, then all images
        inputs = ['-i', audio_file]  # Audio is input 0
        
        for section in sections:
            inputs.extend(['-loop', '1', '-i', section.image_path])
        
        # Build filter complex - prepare each image individually
        filter_parts = []
        
        # Process each image: scale, pad, set duration and fps
        for i, section in enumerate(sections):
            img_input = i + 1  # +1 because audio is input 0
            duration = section.duration
            
            # Scale and crop each image to 1920x1080, set duration and fps
            filter_parts.append(
                f"[{img_input}:v]scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},"
                f"setsar=1,fps={self.fps},"
                f"trim=duration={duration}[v{i}]"
            )
        
        # Concatenate all video segments
        video_inputs = ''.join(f"[v{i}]" for i in range(len(sections)))
        filter_parts.append(f"{video_inputs}concat=n={len(sections)}:v=1:a=0[outv]")
        
        # Join all filter parts with semicolons
        filter_complex = ';'.join(filter_parts)
        
        print(f"Filter complex: {filter_complex}")
        
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            *inputs,  # Audio + all images
            '-filter_complex', filter_complex,
            '-map', '[outv]',  # Use filtered video
            '-map', '0:a',     # Use original audio (input 0)
            '-c:v', 'libx264',
            '-c:a', 'aac', 
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',  # End when audio ends
            output_path
        ]
        
        print("Running FFmpeg command...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            # Fallback to simple single image if complex filter fails
            print("Falling back to single image approach...")
            return self._create_single_image_video(sections[0], audio_file, output_path, progress_callback)
        
        return output_path
    
    def _create_video_with_fade_transitions(self, sections: List[VideoSection], 
                                          audio_file: str, output_path: str,
                                          fade_duration: float = 1.0,
                                          progress_callback=None, 
                                          add_visualizer: bool = True,
                                          visualizer_style: str = "spectrum_waves",
                                          music_analysis: Dict[str, Any] = None) -> str:
        """Create video with fade transitions and audio visualizer"""
        
        print(f"Creating video with fade transitions and visualizer: {len(sections)} sections")
        for i, section in enumerate(sections):
            print(f"  Section {i}: {section.start_time:.1f}s-{section.end_time:.1f}s ({section.duration:.1f}s) - {section.section_type} - {section.image_path}")
        
        # Build inputs: audio first, then all images
        inputs = ['-i', audio_file]  # Audio is input 0
        
        for section in sections:
            inputs.extend(['-loop', '1', '-i', section.image_path])
        
        # Build filter complex with fade transitions and visualizer
        filter_parts = []
        
        # Process each image - use exact section durations without adding fade time
        for i, section in enumerate(sections):
            img_input = i + 1  # +1 because audio is input 0
            duration = section.duration  # Use exact section duration
            
            # Scale, crop, set duration and fps for each image
            filter_parts.append(
                f"[{img_input}:v]scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},"
                f"setsar=1,fps={self.fps},"
                f"trim=duration={duration},setpts=PTS-STARTPTS[img{i}]"
            )
        
        # Create proper sequential concatenation instead of complex xfade
        if len(sections) == 1:
            current_video = "[img0]"
        else:
            # Simple concatenation without overlapping fades for now
            video_inputs = ''.join(f"[img{i}]" for i in range(len(sections)))
            filter_parts.append(f"{video_inputs}concat=n={len(sections)}:v=1:a=0[concatenated]")
            current_video = "[concatenated]"
        
        # Add professional visualizer (clean without overlay background)
        if add_visualizer:
            visualizer_height = 200
            
            # Create a clean blue spectrum visualizer without background
            filter_parts.append(
                f"[0:a]showspectrum=s={self.width}x{visualizer_height}:"
                f"mode=combined:color=intensity:scale=log[spectrum]"
            )
            
            # Apply blue color mapping and make background transparent
            filter_parts.append(
                f"[spectrum]colorchannelmixer="
                f"rr=0.0:rg=0.2:rb=1.0:"
                f"gr=0.0:gg=0.4:gb=1.0:"
                f"br=0.0:bg=0.6:bb=1.0,"
                f"colorkey=0x000000:0.3:0.1[clean_spectrum]"
            )
            
            # Overlay clean visualizer at bottom of video
            filter_parts.append(
                f"{current_video}[clean_spectrum]overlay=0:H-{visualizer_height}[outvid]"
            )
            final_video = "[outvid]"
        else:
            final_video = current_video
        
        # Calculate total duration from music analysis BEFORE building command
        # Use the actual audio duration from the analysis
        if music_analysis and 'duration' in music_analysis:
            total_duration = music_analysis['duration']
            print(f"Using audio duration from analysis: {total_duration}s")
        else:
            total_duration = sum(section.duration for section in sections)
            print(f"Using sum of section durations: {total_duration}s")
        
        print(f"Section count: {len(sections)}, Section total: {sum(section.duration for section in sections)}s")
        
        # Join all filter parts
        filter_complex = ';'.join(filter_parts)
        
        print(f"Filter complex: {filter_complex}")
        
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            *inputs,  # Audio + all images
            '-filter_complex', filter_complex,
            '-map', final_video,  # Use final processed video
            '-map', '0:a',        # Use original audio
            '-c:v', 'libx264',
            '-c:a', 'aac', 
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-t', str(total_duration),  # Set explicit duration instead of -shortest
            '-progress', 'pipe:2',  # Progress to stderr
            '-v', 'info',  # Verbose output
            output_path
        ]
        
        print("Running FFmpeg with fade transitions and visualizer...")
        print(f"Expected total duration: {total_duration} seconds")
        print(f"Command: {' '.join(cmd[:10])}...")  # Show first 10 args
        
        # Run with progress monitoring - read both stdout and stderr
        import time
        import threading
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True)
        print(f"Total video duration: {total_duration} seconds")
        
        output_lines = []
        
        # Read output line by line
        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                line = line.strip()
                output_lines.append(line)
                print(f"FFmpeg: {line}")  # Debug output
                
                if progress_callback:
                    # Parse FFmpeg progress - look for time information
                    if 'time=' in line:
                        try:
                            # Extract time in HH:MM:SS.MS format
                            time_str = line.split('time=')[1].split()[0]
                            if ':' in time_str:
                                parts = time_str.split(':')
                                hours = float(parts[0])
                                minutes = float(parts[1])  
                                seconds = float(parts[2])
                                current_time = hours * 3600 + minutes * 60 + seconds
                                
                                # Calculate real progress (0-100% range for rendering)
                                if total_duration > 0:
                                    progress_percent = min((current_time / total_duration) * 100, 100)
                                    progress_callback(f"Rendering video... {current_time:.1f}s/{total_duration:.1f}s", int(progress_percent))
                        except Exception as e:
                            print(f"Progress parse error: {e}")
                    
                    elif 'frame=' in line:
                        try:
                            # Extract frame number as backup progress indicator
                            frame_str = line.split('frame=')[1].split()[0].strip()
                            current_frame = int(frame_str)
                            total_frames = total_duration * self.fps
                            if total_frames > 0:
                                progress_percent = min((current_frame / total_frames) * 100, 100)
                                progress_callback(f"Rendering video... frame {current_frame}/{int(total_frames)}", int(progress_percent))
                        except Exception as e:
                            print(f"Frame parse error: {e}")
        
        # Get all output for debugging
        full_output = '\n'.join(output_lines)
        
        if process.returncode != 0:
            print(f"FFmpeg failed with output: {full_output}")
            if progress_callback:
                progress_callback("Error occurred, falling back...", 50)
            # Fallback to simple approach
            print("Falling back to simple single image approach...")
            return self._create_single_image_video(sections[0], audio_file, output_path, progress_callback)
        
        # Only mark as complete if we actually processed the full duration
        last_time = 0
        for line in output_lines[-10:]:  # Check last 10 lines for final time
            if 'time=' in line:
                try:
                    time_str = line.split('time=')[1].split()[0]
                    if ':' in time_str:
                        parts = time_str.split(':')
                        last_time = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except:
                    pass
        
        if progress_callback:
            if last_time >= total_duration * 0.95:  # At least 95% completed
                progress_callback("Video generation complete!", 100)
            else:
                progress_callback(f"Video incomplete - stopped at {last_time:.1f}s/{total_duration}s", int((last_time/total_duration)*100))
        
        return output_path
    
    def create_video_with_crossfade(self, sections: List[VideoSection], 
                                  audio_file: str, output_path: str,
                                  crossfade_duration: float = 1.0) -> str:
        """Create video with smooth crossfade transitions between sections"""
        
        if len(sections) <= 1:
            return self._create_single_image_video(sections[0] if sections else None, 
                                                 audio_file, output_path, progress_callback)
        
        # Build complex filter for crossfade transitions
        inputs = ['-i', audio_file]  # Audio first
        filter_parts = []
        
        # Add all images as inputs and prepare them
        for i, section in enumerate(sections):
            inputs.extend(['-loop', '1', '-i', section.image_path])
            
            # Prepare each image: scale, pad, set fps, and duration
            img_index = i + 1  # +1 because audio is input 0
            duration = section.duration + (crossfade_duration if i < len(sections) - 1 else 0)
            
            filter_parts.append(
                f"[{img_index}:v]scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
                f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={self.fps},"
                f"trim=duration={duration}[prep{i}]"
            )
        
        # Create crossfade transitions between consecutive sections
        current_stream = "[prep0]"
        
        for i in range(len(sections) - 1):
            next_stream = f"[prep{i+1}]"
            transition_start = sections[i].duration - crossfade_duration
            
            # Apply crossfade transition
            filter_parts.append(
                f"{current_stream}{next_stream}xfade=transition=fade:"
                f"duration={crossfade_duration}:offset={transition_start}[fade{i}]"
            )
            current_stream = f"[fade{i}]"
        
        # Final output
        filter_parts.append(f"{current_stream}format=yuv420p[outv]")
        
        filter_complex = ';'.join(filter_parts)
        
        cmd = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '0:a',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-shortest',
            output_path
        ]
        
        print(f"Creating video with crossfade transitions...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg crossfade failed: {result.stderr}")
        
        return output_path

class VideoGeneratorGUI:
    """GUI integration methods for video generation"""
    
    @staticmethod
    def validate_inputs(music_analysis: Dict[str, Any], 
                       processed_images_dir: str, 
                       audio_file: str) -> List[str]:
        """Validate inputs for video generation"""
        errors = []
        
        if not music_analysis:
            errors.append("Music analysis data is missing")
        
        if not os.path.exists(processed_images_dir):
            errors.append(f"Processed images directory not found: {processed_images_dir}")
        
        if not os.path.exists(audio_file):
            errors.append(f"Audio file not found: {audio_file}")
        
        # Check if we have processed images
        if os.path.exists(processed_images_dir):
            section_dirs = [d for d in os.listdir(processed_images_dir) 
                           if d.startswith('section_') and 
                           os.path.isdir(os.path.join(processed_images_dir, d))]
            
            if not section_dirs:
                errors.append("No section directories found in processed images")
            else:
                # Check if sections have images
                empty_sections = []
                for section_dir in section_dirs:
                    section_path = os.path.join(processed_images_dir, section_dir)
                    image_files = [f for f in os.listdir(section_path) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    if not image_files:
                        empty_sections.append(section_dir)
                
                if empty_sections:
                    errors.append(f"Empty section directories: {', '.join(empty_sections)}")
        
        return errors

def main():
    """Test video generation"""
    
    # Sample test data
    sample_analysis = {
        "song": "test_song.mp3",
        "duration": 60.0,
        "video_sections": [
            {
                "start": 0.0,
                "end": 20.0,
                "type": "intro",
                "energy": 0.3
            },
            {
                "start": 20.0,
                "end": 40.0,
                "type": "verse",
                "energy": 0.6
            },
            {
                "start": 40.0,
                "end": 60.0,
                "type": "outro",
                "energy": 0.2
            }
        ]
    }
    
    print("Video Generator Test")
    print("===================")
    
    try:
        # Initialize video generator
        generator = VideoGenerator()
        print("* FFmpeg available")
        
        # Test validation
        errors = VideoGeneratorGUI.validate_inputs(
            sample_analysis,
            "processed_images",
            "test_audio.mp3"
        )
        
        if errors:
            print("Validation errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("* Input validation passed")
            
        print("\nVideo generator ready for integration!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()