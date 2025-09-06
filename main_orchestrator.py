import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import json
import subprocess
from pathlib import Path
import sys

# Try to import drag and drop functionality
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# Import existing modules
from video_generator import VideoGenerator
from image_manager import UnsplashImageManager, ImageProcessor
from llm_integration import LocalLLMManager, EnhancedImageManager
import librosa
import numpy as np


class MainOrchestrator:
    """Main Orchestrator - Single page GUI for complete music video pipeline"""
    
    def __init__(self, root):
        self.root = root
            
        self.root.title("Music Video Generator - Complete Pipeline")
        self.root.geometry("800x900")
        
        # 60-30-10 Color Scheme with Blue as main
        self.colors = {
            'primary_blue': '#2196F3',      # 60% - Main blue
            'dark_gray': '#424242',         # 30% - Secondary dark gray  
            'light_accent': '#E3F2FD',      # 10% - Light blue accent
            'black': '#000000',
            'white': '#FFFFFF',
            'success': '#4CAF50',
            'error': '#F44336'
        }
        
        self.root.configure(bg=self.colors['black'])
        
        # Audio file paths
        self.original_file = None
        self.instrumental_file = None
        self.vocal_file = None
        
        # Processing status
        self.is_processing = False
        
        # Initialize video generator (core requirement)
        self.video_generator = VideoGenerator(output_resolution=(1920, 1080), fps=30)
        
        # Flag for module availability (will check after UI is created)
        self.modules_available = True
        
        self.create_ui()
    
    def create_ui(self):
        """Create the single-page UI"""
        
        # Main container with padding
        main_frame = tk.Frame(self.root, bg=self.colors['black'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="🎵 Music Video Generator",
            font=('Arial', 24, 'bold'),
            fg=self.colors['primary_blue'],
            bg=self.colors['black']
        )
        title_label.pack(pady=(0, 30))
        
        # Subtitle
        subtitle_label = tk.Label(
            main_frame,
            text="Drop 3 audio files → Click Generate → Get your music video",
            font=('Arial', 12),
            fg=self.colors['dark_gray'],
            bg=self.colors['black']
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Audio Files Section
        self.create_audio_section(main_frame)
        
        # Progress Section
        self.create_progress_section(main_frame)
        
        # Generate Button
        self.create_generate_button(main_frame)
        
        # Status Section
        self.create_status_section(main_frame)
    
    def create_audio_section(self, parent):
        """Create compact audio file drop zones"""
        
        audio_frame = tk.Frame(parent, bg=self.colors['black'])
        audio_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Section title
        section_title = tk.Label(
            audio_frame,
            text="📁 Audio Files (Required)",
            font=('Arial', 16, 'bold'),
            fg=self.colors['primary_blue'],
            bg=self.colors['black']
        )
        section_title.pack(anchor='w', pady=(0, 15))
        
        # Create 3 compact drop zones in a row
        drop_frame = tk.Frame(audio_frame, bg=self.colors['black'])
        drop_frame.pack(fill=tk.X)
        
        # Original Audio
        self.original_frame = self.create_drop_zone(
            drop_frame, "Original Audio", "🎵", 
            lambda: self.select_file('original')
        )
        self.original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Instrumental Audio  
        self.instrumental_frame = self.create_drop_zone(
            drop_frame, "Instrumental", "🎼",
            lambda: self.select_file('instrumental')
        )
        self.instrumental_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 5))
        
        # Vocal Audio
        self.vocal_frame = self.create_drop_zone(
            drop_frame, "Vocal Track", "🎤",
            lambda: self.select_file('vocal')
        )
        self.vocal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
    
    def create_drop_zone(self, parent, title, icon, command):
        """Create a compact drop zone for audio files with drag and drop"""
        
        frame = tk.Frame(
            parent, 
            bg=self.colors['dark_gray'],
            relief=tk.RAISED,
            bd=2
        )
        
        # Icon and title
        icon_label = tk.Label(
            frame,
            text=icon,
            font=('Arial', 20),
            bg=self.colors['dark_gray'],
            fg=self.colors['primary_blue']
        )
        icon_label.pack(pady=(15, 5))
        
        title_label = tk.Label(
            frame,
            text=title,
            font=('Arial', 10, 'bold'),
            bg=self.colors['dark_gray'],
            fg=self.colors['white']
        )
        title_label.pack(pady=(0, 5))
        
        # File name label with drag instructions
        filename_label = tk.Label(
            frame,
            text="📁 Drop file here\nor click Browse",
            font=('Arial', 8),
            bg=self.colors['dark_gray'],
            fg=self.colors['light_accent'],
            wraplength=120,
            justify=tk.CENTER
        )
        filename_label.pack(pady=(0, 10))
        
        # Browse button
        browse_btn = tk.Button(
            frame,
            text="Browse",
            command=command,
            bg=self.colors['primary_blue'],
            fg=self.colors['white'],
            font=('Arial', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=5
        )
        browse_btn.pack(pady=(0, 15))
        
        # Enable Windows-compatible drag and drop
        file_type = title.lower().replace(' ', '_').replace('track', '').strip('_')
        self.enable_drop(frame, file_type)
        
        # Visual feedback for mouse hover (simulates drag feedback)
        def on_enter(event):
            if not getattr(frame, 'has_file', False):
                frame.config(bg=self.colors['primary_blue'], relief=tk.SUNKEN)
                filename_label.config(bg=self.colors['primary_blue'])
            
        def on_leave(event):
            if not getattr(frame, 'has_file', False):
                frame.config(bg=self.colors['dark_gray'], relief=tk.RAISED)
                filename_label.config(bg=self.colors['dark_gray'])
        
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        
        # Store reference to filename label and file type
        frame.filename_label = filename_label
        frame.file_type = file_type
        
        return frame
    
    def create_progress_section(self, parent):
        """Create progress tracking section"""
        
        progress_frame = tk.Frame(parent, bg=self.colors['black'])
        progress_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Progress title
        progress_title = tk.Label(
            progress_frame,
            text="⚙️ Processing Pipeline",
            font=('Arial', 16, 'bold'),
            fg=self.colors['primary_blue'],
            bg=self.colors['black']
        )
        progress_title.pack(anchor='w', pady=(0, 15))
        
        # Progress steps
        steps_frame = tk.Frame(progress_frame, bg=self.colors['black'])
        steps_frame.pack(fill=tk.X)
        
        self.step_labels = []
        steps = [
            "1. Audio Processing & Smart Balancing",
            "2. Video Generation with Circular Visualizer"
        ]
        
        for i, step in enumerate(steps):
            step_label = tk.Label(
                steps_frame,
                text=f"⏳ {step}",
                font=('Arial', 10),
                fg=self.colors['dark_gray'],
                bg=self.colors['black'],
                anchor='w'
            )
            step_label.pack(fill=tk.X, pady=2)
            self.step_labels.append(step_label)
        
        # Overall progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            style="Blue.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=(15, 0))
        
        # Configure progress bar style
        style = ttk.Style()
        style.configure(
            "Blue.Horizontal.TProgressbar",
            troughcolor=self.colors['dark_gray'],
            background=self.colors['primary_blue'],
            borderwidth=0,
            lightcolor=self.colors['primary_blue'],
            darkcolor=self.colors['primary_blue']
        )
    
    def create_generate_button(self, parent):
        """Create the main generate button"""
        
        button_frame = tk.Frame(parent, bg=self.colors['black'])
        button_frame.pack(pady=30)
        
        self.generate_btn = tk.Button(
            button_frame,
            text="🚀 Generate Music Video",
            command=self.start_generation,
            font=('Arial', 18, 'bold'),
            bg=self.colors['primary_blue'],
            fg=self.colors['white'],
            relief=tk.FLAT,
            padx=40,
            pady=15,
            state=tk.DISABLED
        )
        self.generate_btn.pack()
        
        # Update button state based on file selection
        self.update_generate_button()
    
    def create_status_section(self, parent):
        """Create status display section"""
        
        status_frame = tk.Frame(parent, bg=self.colors['black'])
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status title
        status_title = tk.Label(
            status_frame,
            text="📊 Status",
            font=('Arial', 16, 'bold'),
            fg=self.colors['primary_blue'],
            bg=self.colors['black']
        )
        status_title.pack(anchor='w', pady=(0, 15))
        
        # Status text area
        self.status_text = tk.Text(
            status_frame,
            height=8,
            bg=self.colors['dark_gray'],
            fg=self.colors['white'],
            font=('Consolas', 9),
            relief=tk.FLAT,
            padx=15,
            pady=10
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Add initial status with drag and drop info
        if DND_AVAILABLE:
            self.update_status("✅ Drag & Drop enabled! Drop audio files onto the zones above or use Browse buttons.")
        else:
            self.update_status("Ready. Use Browse buttons to select 3 audio files to begin.")
            
        # Check module availability after UI is created
        self.check_modules()
    
    def check_modules(self):
        """Check if additional modules are available"""
        try:
            # Try to initialize modules (like the working beta version)
            from image_manager import UnsplashImageManager, ImageProcessor
            from llm_integration import LocalLLMManager, EnhancedImageManager
            
            # Don't actually initialize with API keys, just check if they can be imported
            self.modules_available = True
            self.update_status("✅ All modules available for live image generation")
            
        except ImportError as e:
            self.modules_available = False
            self.update_status(f"⚠️ Some modules not available: {e}")
        except Exception as e:
            # API key issues, etc - but modules are available
            self.modules_available = True
            self.update_status("✅ Modules available (API configuration may be needed)")
    
    def enable_drop(self, widget, file_type):
        """Enable drag and drop if available"""
        if DND_AVAILABLE:
            try:
                # Register widget for file drops
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind('<<Drop>>', lambda e: self.handle_drop(e, file_type))
                widget.dnd_bind('<<DragEnter>>', lambda e: self.on_drag_enter(widget))
                widget.dnd_bind('<<DragLeave>>', lambda e: self.on_drag_leave(widget))
                return True
            except Exception as e:
                self.update_status(f"Drag & drop setup failed: {e}")
                return False
        else:
            # Show message about missing drag and drop
            if not hasattr(self, 'dnd_message_shown'):
                self.update_status("💡 Install tkinterdnd2 for drag & drop: pip install tkinterdnd2")
                self.dnd_message_shown = True
            return False
    
    def on_drag_enter(self, widget):
        """Visual feedback when dragging over"""
        if not getattr(widget, 'has_file', False):
            widget.config(bg=self.colors['primary_blue'], relief=tk.SUNKEN)
            widget.filename_label.config(bg=self.colors['primary_blue'], text="Drop here!")
    
    def on_drag_leave(self, widget):
        """Visual feedback when dragging away"""  
        if not getattr(widget, 'has_file', False):
            widget.config(bg=self.colors['dark_gray'], relief=tk.RAISED)
            widget.filename_label.config(bg=self.colors['dark_gray'], text="📁 Drop file here\nor click Browse")
    
    def handle_drop(self, event, file_type):
        """Handle drag and drop of audio files"""
        try:
            # Get the dropped file paths (tkinterdnd2 format)
            if hasattr(event, 'data'):
                files = self.root.tk.splitlist(event.data)
            else:
                files = [event]
                
            if files:
                filename = files[0]  # Take the first file
                
                # Clean up the file path
                filename = filename.strip('{}').strip('"')
                
                # Check if it's an audio file
                audio_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma']
                if any(filename.lower().endswith(ext) for ext in audio_extensions):
                    self.set_audio_file(file_type, filename)
                    self.update_status(f"🎵 Dropped: {os.path.basename(filename)}")
                else:
                    messagebox.showwarning("Invalid File", f"Please drop an audio file.\nSupported: {', '.join(audio_extensions)}")
                    
        except Exception as e:
            self.update_status(f"Drop error: {e}")
            print(f"Debug - Drop event: {event}, data: {getattr(event, 'data', 'no data')}")
    
    def set_audio_file(self, file_type, filename):
        """Set audio file and update UI"""
        
        if file_type == 'original' or file_type == 'original_audio':
            self.original_file = filename
            self.original_frame.filename_label.config(text=os.path.basename(filename))
            self.original_frame.config(highlightbackground=self.colors['primary_blue'], highlightthickness=3, bg=self.colors['black'])
            self.original_frame.has_file = True
        elif file_type == 'instrumental':
            self.instrumental_file = filename  
            self.instrumental_frame.filename_label.config(text=os.path.basename(filename))
            self.instrumental_frame.config(highlightbackground=self.colors['primary_blue'], highlightthickness=3, bg=self.colors['black'])
            self.instrumental_frame.has_file = True
        elif file_type == 'vocal' or file_type == 'vocal_':
            self.vocal_file = filename
            self.vocal_frame.filename_label.config(text=os.path.basename(filename))
            self.vocal_frame.config(highlightbackground=self.colors['primary_blue'], highlightthickness=3, bg=self.colors['black'])
            self.vocal_frame.has_file = True
        
        self.update_generate_button()
        self.update_status(f"✅ Added {file_type}: {os.path.basename(filename)}")
    
    def select_file(self, file_type):
        """Handle file selection via browse button"""
        
        filename = filedialog.askopenfilename(
            title=f"Select {file_type.title()} Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.flac *.m4a *.aac *.ogg"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            self.set_audio_file(file_type, filename)
    
    def update_generate_button(self):
        """Update generate button state based on file selection"""
        
        if all([self.original_file, self.instrumental_file, self.vocal_file]) and not self.is_processing:
            self.generate_btn.config(state=tk.NORMAL, bg=self.colors['success'])
        else:
            self.generate_btn.config(state=tk.DISABLED, bg=self.colors['dark_gray'])
    
    def update_status(self, message):
        """Update status display"""
        
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, step, progress, message=""):
        """Update progress display"""
        
        # Update step status
        for i, label in enumerate(self.step_labels):
            if i < step:
                label.config(text=f"✅ {label.cget('text')[2:]}", fg=self.colors['success'])
            elif i == step:
                label.config(text=f"⚙️ {label.cget('text')[2:]}", fg=self.colors['primary_blue'])
            else:
                label.config(text=f"⏳ {label.cget('text')[2:]}", fg=self.colors['dark_gray'])
        
        # Update progress bar (2 steps instead of 4)
        total_progress = (step * 50) + (progress * 0.5)
        self.progress_var.set(total_progress)
        
        if message:
            self.update_status(message)
    
    def start_generation(self):
        """Start the complete music video generation pipeline"""
        
        if self.is_processing:
            return
        
        self.is_processing = True
        self.generate_btn.config(state=tk.DISABLED, text="Processing...", bg=self.colors['dark_gray'])
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.run_pipeline)
        thread.daemon = True
        thread.start()
    
    def run_pipeline(self):
        """Run the complete pipeline"""
        
        try:
            # Step 1: Audio Processing & Alignment
            self.update_progress(0, 0, "Starting audio processing...")
            
            # Process and align all 3 audio files
            mixed_audio = self.process_and_align_audio(
                self.original_file,
                self.instrumental_file,
                self.vocal_file
            )
            
            self.update_progress(0, 100, "✅ Audio processing complete")
            
            # Step 2: Video Rendering with Circular Visualizer
            self.update_progress(1, 0, "Creating circular audio visualizer...")
            
            # Generate video with background.png and circular blue visualizer
            output_video = self.generate_circular_visualizer_video(mixed_audio)
            
            self.update_progress(1, 100, f"✅ Video generation complete: {output_video}")
            
            # Clean up section_images after successful video production
            self.cleanup_after_video()
            
            # Show completion message
            messagebox.showinfo("Success!", f"Music video generated successfully!\n\nSaved as: {output_video}")
            
        except Exception as e:
            self.update_status(f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred during processing:\n\n{str(e)}")
        
        finally:
            self.is_processing = False
            self.generate_btn.config(
                state=tk.NORMAL, 
                text="🚀 Generate Music Video", 
                bg=self.colors['success']
            )
    
    def process_and_align_audio(self, original_file, instrumental_file, vocal_file):
        """Process and align audio exactly like audio_processor_gui.py"""
        
        try:
            # Import the working AudioProcessor class
            from audio_processor_gui import AudioProcessor
            
            self.update_status("🎵 Loading audio files...")
            
            # Load audio files at 44100 Hz (exact same as beta)
            original, sr1 = librosa.load(original_file, sr=44100)
            instrumental, sr2 = librosa.load(instrumental_file, sr=44100) 
            vocal, sr3 = librosa.load(vocal_file, sr=44100)
            
            self.update_status("⚙️ Aligning vocal track to original...")
            
            # Use the exact same AudioProcessor from beta
            processor = AudioProcessor()
            
            # Align vocal to original reference (same as beta)
            aligned_vocal = processor.align_audio(original, vocal)
            
            self.update_status("🎛️ Smart balancing and mixing audio...")
            
            # Mix with intelligent auto-balancing for mixed sources (AI-separated + karaoke)
            final_audio = processor.mix_audio(instrumental, aligned_vocal)
            
            self.update_status("💾 Saving processed audio...")
            
            # Save the mixed result
            output_path = "processed_audio.wav"
            import soundfile as sf
            sf.write(output_path, final_audio, 44100)
            
            return output_path
            
        except Exception as e:
            self.update_status(f"❌ Audio processing error: {e}")
            # Fallback to original file
            return original_file
    
    def _run_ffmpeg_with_progress(self, cmd, duration, description):
        """Run FFmpeg command with simple status updates"""
        
        self.update_status(f"⚙️ {description}...")
        
        # Run FFmpeg normally without complex progress parsing
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            raise Exception(f"{description} failed: {result.stderr}")
        
        self.update_status(f"✅ {description} complete!")
    
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

    def analyze_music(self, audio_file):
        """Real music analysis using librosa"""
        
        try:
            self.update_status("🎼 Analyzing music characteristics...")
            
            # Load audio
            y, sr = librosa.load(audio_file)
            duration = librosa.get_duration(y=y, sr=sr)
            
            self.update_status("🎯 Detecting tempo and beats...")
            
            # Tempo detection
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            self.update_status("🔍 Analyzing spectral features...")
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            
            # Energy analysis
            rms = librosa.feature.rms(y=y)
            energy = np.mean(rms)
            
            # Create sections based on beat analysis
            beat_times = librosa.frames_to_time(beats, sr=sr)
            
            # Simple sectioning - could be improved with onset detection
            sections = []
            section_types = ['intro', 'verse', 'chorus', 'verse', 'chorus', 'bridge', 'chorus', 'outro']
            
            if len(beat_times) > len(section_types):
                section_boundaries = np.linspace(0, duration, len(section_types) + 1)
                
                for i, section_type in enumerate(section_types):
                    start_time = section_boundaries[i]
                    end_time = section_boundaries[i + 1]
                    
                    sections.append({
                        'start': start_time,
                        'end': end_time, 
                        'type': section_type,
                        'energy': float(energy) * (0.7 + 0.3 * np.random.random())
                    })
            
            self.update_status("✅ Music analysis complete!")
            
            return {
                'duration': duration,
                'video_sections': sections,
                'tempo': float(tempo),
                'key': 'C',  # Could add key detection
                'energy': float(energy),
                'spectral_centroid': float(np.mean(spectral_centroids))
            }
            
        except Exception as e:
            self.update_status(f"⚠️ Music analysis error: {e}, using fallback")
            # Fallback to simple analysis
            return self.simple_music_analysis(audio_file)

    def simple_music_analysis(self, audio_file):
        """Fallback simple analysis"""
        try:
            y, sr = librosa.load(audio_file)
            duration = librosa.get_duration(y=y, sr=sr)
        except:
            duration = 180  # Default fallback
        
        sections = []
        section_types = ['intro', 'verse', 'chorus', 'verse', 'chorus', 'bridge', 'chorus', 'outro']
        section_duration = duration / len(section_types)
        
        for i, section_type in enumerate(section_types):
            sections.append({
                'start': i * section_duration,
                'end': (i + 1) * section_duration,
                'type': section_type,
                'energy': 0.5 + (i % 3) * 0.2
            })
        
        return {
            'duration': duration,
            'video_sections': sections,
            'tempo': 120,
            'key': 'C',
            'energy': 0.7
        }
    
    def generate_images(self, analysis):
        """Generate images exactly like audio_processor_gui.py"""
        
        images_dir = "section_images"
        
        # Always clean up existing images first (no reuse)
        if os.path.exists(images_dir):
            import shutil
            self.update_status("🗑️ Removing old images...")
            shutil.rmtree(images_dir)
        
        # Create fresh directory
        os.makedirs(images_dir, exist_ok=True)
        
        try:
            self.update_status("🎨 Initializing Unsplash image manager...")
            
            # Import the working modules exactly like the beta
            from image_manager import UnsplashImageManager
            from llm_integration import LocalLLMManager, EnhancedImageManager
            
            # Load API key from .env file (same as beta does)
            api_key = ""
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('UNSPLASH_API='):
                            api_key = line.split('=', 1)[1].strip().strip('"')
                            break
            except:
                pass
            
            # Fallback to environment variable if .env not found
            if not api_key:
                api_key = os.getenv('UNSPLASH_ACCESS_KEY', '')
                
            if not api_key:
                self.update_status("❌ No Unsplash API key found")
                self.update_status("💡 Please add UNSPLASH_API=your_key to .env file")
                self.update_status("💡 Get free key at: https://unsplash.com/developers")
                raise Exception("Unsplash API key not configured")
            
            # Initialize modules exactly like the beta does
            try:
                # Create managers with API key (same as beta)
                self.update_status("🔑 Found Unsplash API key, initializing...")
                image_manager = UnsplashImageManager(api_key)
                llm_manager = LocalLLMManager()
                
                self.update_status("🧠 Using LLM for intelligent image selection...")
                
                # Initialize enhanced image manager with LLM (same as beta)
                enhanced_image_manager = EnhancedImageManager(image_manager, llm_manager)
                
                # Use LLM-powered intelligent search (same method as beta)
                sections_images = enhanced_image_manager.search_intelligent_images(
                    analysis,
                    images_per_section=1
                )
                
                self.update_status("✨ LLM-powered image search completed!")
                
                # Download the images (same as beta)
                self.update_status("📥 Downloading selected images...")
                downloaded_paths = image_manager.download_section_images(sections_images)
                
                self.update_status("🖼️ Processing images for video compatibility...")
                
                # Process images for video (same as beta) 
                from image_manager import ImageProcessor
                processed_count = 0
                
                for section_key, image_paths in downloaded_paths.items():
                    if image_paths:
                        section_dir = os.path.join(images_dir, section_key)
                        processed_paths = ImageProcessor.process_section_images(image_paths, section_dir)
                        processed_count += len(processed_paths)
                        section_num = section_key.split('_')[1]
                        self.update_status(f"Section {int(section_num)+1}: {len(processed_paths)} images processed")
                
                self.update_status(f"✅ {processed_count} fresh Unsplash images ready!")
                return images_dir
                
            except Exception as api_error:
                self.update_status(f"⚠️ API/LLM issue: {api_error}")
                self.update_status("💡 Make sure LMStudio is running on localhost:1234")
                # Continue to fallback
                
        except Exception as e:
            self.update_status(f"❌ Image generation error: {e}")
            if "API key" in str(e):
                self.update_status("🔧 SETUP REQUIRED:")
                self.update_status("1. Get free Unsplash API key: https://unsplash.com/developers") 
                self.update_status("2. Set environment variable: UNSPLASH_ACCESS_KEY=your_key")
                self.update_status("3. Install and run LMStudio with a model")
        
        # Fallback: create basic structure but warn user
        self.update_status("⚠️ Image generation failed - creating empty structure")
        self.update_status("❌ Video generation will fail without images!")
        self.update_status("🎯 SOLUTION: Configure Unsplash API + LMStudio, then try again")
        
        for i in range(len(analysis['video_sections'])):
            section_dir = os.path.join(images_dir, f"section_{i}")
            os.makedirs(section_dir, exist_ok=True)
            # Create a placeholder file so user knows what happened
            with open(os.path.join(section_dir, "README.txt"), "w") as f:
                f.write("This directory is empty because image generation failed.\n")
                f.write("Please configure Unsplash API and LMStudio for automatic image download.")
        
        return images_dir
    
    def verify_images_exist(self, images_path):
        """Verify that images were actually generated in section directories"""
        
        if not os.path.exists(images_path):
            self.update_status(f"❌ Images directory doesn't exist: {images_path}")
            return False
        
        # Check each section directory for actual image files
        found_images = 0
        section_dirs = [d for d in os.listdir(images_path) if os.path.isdir(os.path.join(images_path, d)) and d.startswith('section_')]
        
        if not section_dirs:
            self.update_status("❌ No section directories found")
            return False
        
        for section_dir in section_dirs:
            section_path = os.path.join(images_path, section_dir)
            image_files = [f for f in os.listdir(section_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            
            if image_files:
                found_images += len(image_files)
                self.update_status(f"✅ {section_dir}: {len(image_files)} images found")
            else:
                self.update_status(f"⚠️ {section_dir}: No images found")
        
        if found_images == 0:
            self.update_status("❌ No images found in any section directories")
            return False
        
        self.update_status(f"✅ Total images verified: {found_images}")
        return True
    
    def cleanup_after_video(self):
        """Clean up section_images folder after successful video production"""
        
        try:
            import shutil
            
            images_dir = "section_images"
            if os.path.exists(images_dir):
                self.update_status("🧹 Cleaning up image files...")
                shutil.rmtree(images_dir)
                self.update_status("✅ Image cleanup complete!")
            
            # Also clean up any temporary audio files
            temp_files = ["processed_audio.wav"]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.update_status(f"🗑️ Removed temporary file: {temp_file}")
                    
        except Exception as e:
            self.update_status(f"⚠️ Cleanup warning: {e}")
    
    def generate_video(self, analysis, images_path, audio_file):
        """Generate final video"""
        
        output_path = "final_music_video.mp4"
        
        # Use video generator with 1080p 30fps
        return self.video_generator.create_video_from_analysis(
            analysis,
            images_path,
            audio_file,
            output_path,
            transition_duration=1.0,
            progress_callback=lambda msg, pct: self.update_status(f"Video: {msg}"),
            add_visualizer=True,
            use_fade_transitions=True
        )


def main():
    """Main entry point"""
    # Create root window with drag and drop support if available
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
        
    app = MainOrchestrator(root)
    root.mainloop()


if __name__ == "__main__":
    main()