import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import json
from datetime import datetime

# Try to import audio processing libraries
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False

try:
    import librosa
    import numpy as np
    from scipy import signal
    import soundfile as sf
    from dataclasses import dataclass
    from typing import List, Dict, Any
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False

try:
    from image_manager import UnsplashImageManager, ImageProcessor
    from llm_integration import LocalLLMManager, EnhancedImageManager
    from video_generator import VideoGenerator, VideoGeneratorGUI
    IMAGE_LIBS_AVAILABLE = True
except ImportError:
    IMAGE_LIBS_AVAILABLE = False

class AudioProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Audio Processor - Audio Processing & Analysis")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        self.root.configure(bg="#2b2b2b")
        
        # Make window resizable and responsive
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # File paths
        self.original_file = ""
        self.instrumental_file = ""
        self.vocal_file = ""
        self.output_file = ""
        
        # Analysis data
        self.music_analysis = None
        self.analysis_json = None
        
        # Image management data
        self.image_manager = None
        self.llm_manager = None
        self.enhanced_image_manager = None
        self.sections_images = None
        self.downloaded_paths = None
        
        # Video generation data
        self.video_generator = None
        self.video_output_path = None
        
        # Check dependencies
        self.check_dependencies()
        self.setup_gui()
        
    def check_dependencies(self):
        """Check if required libraries are available"""
        missing = []
        if not AUDIO_LIBS_AVAILABLE:
            missing.append("Audio processing libraries (librosa, numpy, scipy, soundfile)")
        if not DRAG_DROP_AVAILABLE:
            missing.append("Drag & drop support (tkinterdnd2)")
            
        if missing:
            missing_text = "\n".join(f"• {lib}" for lib in missing)
            response = messagebox.askyesno(
                "Missing Dependencies", 
                f"The following libraries are missing:\n\n{missing_text}\n\n" +
                "The GUI will work in limited mode. Would you like to:\n" +
                "• YES: Continue in limited mode (browse files only)\n" +
                "• NO: Exit and install dependencies first\n\n" +
                "To install: Run 'install_dependencies.bat' as Administrator"
            )
            if not response:
                self.root.quit()
                return
        
    def setup_gui(self):
        # Create main container with tabs
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")
        
        # Create tabs
        self.audio_tab = ttk.Frame(self.notebook)
        self.analysis_tab = ttk.Frame(self.notebook)
        self.image_tab = ttk.Frame(self.notebook)
        self.video_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.audio_tab, text="1. Audio Processing")
        self.notebook.add(self.analysis_tab, text="2. Music Analysis")
        self.notebook.add(self.image_tab, text="3. Image Management")
        self.notebook.add(self.video_tab, text="4. Video Generation")
        
        # Setup each tab
        self.setup_audio_tab()
        self.setup_analysis_tab()
        self.setup_image_tab()
        self.setup_video_tab()
        
    def setup_audio_tab(self):
        # Configure audio tab grid
        self.audio_tab.grid_rowconfigure(1, weight=1)
        self.audio_tab.grid_columnconfigure(0, weight=1)
        
        # Title and instructions
        title_frame = tk.Frame(self.audio_tab, bg="#2b2b2b")
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(
            title_frame,
            text="Audio Processing - Sync & Mix",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#2b2b2b"
        )
        title_label.grid(row=0, column=0)
        
        instructions = tk.Label(
            title_frame,
            text="Drag and drop MP3 files or click to browse. Output: Synced instrumental + vocal",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#2b2b2b"
        )
        instructions.grid(row=1, column=0, pady=5)
        
        # File input container
        files_frame = tk.Frame(self.audio_tab, bg="#2b2b2b")
        files_frame.grid(row=1, column=0, sticky="nsew", padx=20)
        files_frame.grid_rowconfigure(0, weight=1)
        files_frame.grid_rowconfigure(1, weight=1)
        files_frame.grid_rowconfigure(2, weight=1)
        files_frame.grid_columnconfigure(0, weight=1)
        
        # File input sections
        self.create_file_section(files_frame, "Original Music (with vocals + instruments)", 0)
        self.create_file_section(files_frame, "Instrumental Only", 1)  
        self.create_file_section(files_frame, "Vocal Only", 2)
        
        # Progress and control section
        control_frame = tk.Frame(self.audio_tab, bg="#2b2b2b")
        control_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        control_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_frame = tk.Frame(control_frame, bg="#2b2b2b")
        self.progress_frame.grid(row=0, column=0, sticky="ew", pady=10)
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = tk.Label(
            self.progress_frame,
            text="Ready to process",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#2b2b2b"
        )
        self.progress_label.grid(row=0, column=0)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=10, padx=50)
        
        # Button frame
        button_frame = tk.Frame(control_frame, bg="#2b2b2b")
        button_frame.grid(row=1, column=0, pady=10)
        
        # Process button
        self.process_btn = tk.Button(
            button_frame,
            text="Process Audio",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.process_audio,
            height=2,
            width=15
        )
        self.process_btn.grid(row=0, column=0, padx=10)
        
        # Analyze button  
        self.analyze_btn = tk.Button(
            button_frame,
            text="Analyze Music",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.analyze_music,
            height=2,
            width=15
        )
        self.analyze_btn.grid(row=0, column=1, padx=10)
        
        # Next step button
        self.next_analysis_btn = tk.Button(
            button_frame,
            text="Next: Analysis →",
            font=("Arial", 12, "bold"),
            bg="#9C27B0",
            fg="white",
            command=self.go_to_analysis,
            height=2,
            width=15,
            state="disabled"
        )
        self.next_analysis_btn.grid(row=0, column=2, padx=10)
        
        # Output section
        self.output_frame = tk.Frame(control_frame, bg="#2b2b2b")
        self.output_frame.grid(row=2, column=0, sticky="ew", pady=20)
        self.output_frame.grid_columnconfigure(1, weight=1)
        
        output_label = tk.Label(
            self.output_frame,
            text="Output File:",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#2b2b2b"
        )
        output_label.grid(row=0, column=0, sticky="w")
        
        self.output_path_label = tk.Label(
            self.output_frame,
            text="No output yet",
            font=("Arial", 9),
            fg="#cccccc",
            bg="#2b2b2b",
            wraplength=800,
            justify="left"
        )
        self.output_path_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
    def create_file_section(self, parent, title, index):
        frame = tk.Frame(parent, bg="#3b3b3b", relief="raised", bd=2)
        frame.grid(row=index, column=0, pady=10, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = tk.Label(
            frame,
            text=title,
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#3b3b3b"
        )
        title_label.grid(row=0, column=0, pady=10)
        
        # Drop zone
        drop_frame = tk.Frame(frame, bg="#4b4b4b", height=80)
        drop_frame.grid(row=1, column=0, pady=10, padx=20, sticky="ew")
        drop_frame.grid_rowconfigure(0, weight=1)
        drop_frame.grid_columnconfigure(0, weight=1)
        drop_frame.grid_propagate(False)
        
        drop_label = tk.Label(
            drop_frame,
            text="Drag MP3 file here or click to browse",
            font=("Arial", 10),
            fg="#aaaaaa",
            bg="#4b4b4b"
        )
        drop_label.grid(row=0, column=0)
        
        # File path label
        file_label = tk.Label(
            frame,
            text="No file selected",
            font=("Arial", 9),
            fg="#cccccc",
            bg="#3b3b3b",
            wraplength=800,
            justify="left"
        )
        file_label.grid(row=2, column=0, pady=5, padx=20, sticky="w")
        
        # Store references
        if index == 0:
            self.original_drop_frame = drop_frame
            self.original_file_label = file_label
        elif index == 1:
            self.instrumental_drop_frame = drop_frame
            self.instrumental_file_label = file_label
        else:
            self.vocal_drop_frame = drop_frame
            self.vocal_file_label = file_label
        
        # Setup drag and drop if available
        if DRAG_DROP_AVAILABLE:
            drop_frame.drop_target_register(DND_FILES)
            drop_frame.dnd_bind('<<Drop>>', lambda e, idx=index: self.on_drop(e, idx))
        
        # Setup click to browse
        drop_frame.bind("<Button-1>", lambda e, idx=index: self.browse_file(idx))
        drop_label.bind("<Button-1>", lambda e, idx=index: self.browse_file(idx))
        
    def setup_analysis_tab(self):
        """Setup the music analysis tab"""
        self.analysis_tab.grid_rowconfigure(1, weight=1)
        self.analysis_tab.grid_columnconfigure(0, weight=1)
        
        # Title
        title_frame = tk.Frame(self.analysis_tab, bg="#2b2b2b")
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(
            title_frame,
            text="Music Analysis & JSON Export",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#2b2b2b"
        )
        title_label.grid(row=0, column=0)
        
        instructions = tk.Label(
            title_frame,
            text="Analyze audio characteristics for intelligent image selection and video generation",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#2b2b2b"
        )
        instructions.grid(row=1, column=0, pady=5)
        
        # Analysis content area
        content_frame = tk.Frame(self.analysis_tab, bg="#2b2b2b")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # File selection for analysis
        file_frame = tk.Frame(content_frame, bg="#3b3b3b", relief="raised", bd=2)
        file_frame.grid(row=0, column=0, sticky="ew", pady=10)
        file_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            file_frame,
            text="File to Analyze:",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.analysis_file_var = tk.StringVar(value="Select processed audio file or original")
        self.analysis_file_label = tk.Label(
            file_frame,
            textvariable=self.analysis_file_var,
            font=("Arial", 10),
            fg="#cccccc",
            bg="#3b3b3b",
            wraplength=600
        )
        self.analysis_file_label.grid(row=1, column=0, columnspan=3, padx=20, sticky="ew")
        
        # Browse button for analysis file
        tk.Button(
            file_frame,
            text="Browse Audio File",
            font=("Arial", 10),
            bg="#555555",
            fg="white",
            command=self.browse_analysis_file,
            width=15
        ).grid(row=0, column=1, padx=10, pady=10)
        
        # Use processed file button
        self.use_processed_btn = tk.Button(
            file_frame,
            text="Use Processed File",
            font=("Arial", 10),
            bg="#666666",
            fg="white",
            command=self.use_processed_file,
            width=15,
            state="disabled"
        )
        self.use_processed_btn.grid(row=0, column=2, padx=10, pady=10)
        
        # Analysis results area
        results_frame = tk.Frame(content_frame, bg="#2b2b2b")
        results_frame.grid(row=1, column=0, sticky="nsew", pady=10)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # JSON display with scrolling
        self.json_display = scrolledtext.ScrolledText(
            results_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD,
            state="disabled"
        )
        self.json_display.grid(row=0, column=0, sticky="nsew")
        
        # Control buttons for analysis
        analysis_buttons = tk.Frame(content_frame, bg="#2b2b2b")
        analysis_buttons.grid(row=2, column=0, pady=20)
        
        tk.Button(
            analysis_buttons,
            text="Analyze Audio",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            command=self.run_music_analysis,
            height=2,
            width=15
        ).grid(row=0, column=0, padx=10)
        
        self.export_json_btn = tk.Button(
            analysis_buttons,
            text="Export JSON",
            font=("Arial", 12, "bold"),
            bg="#9C27B0",
            fg="white",
            command=self.export_analysis_json,
            height=2,
            width=15,
            state="disabled"
        )
        self.export_json_btn.grid(row=0, column=1, padx=10)
        
        tk.Button(
            analysis_buttons,
            text="Clear Analysis",
            font=("Arial", 12, "bold"),
            bg="#F44336",
            fg="white",
            command=self.clear_analysis,
            height=2,
            width=15
        ).grid(row=0, column=2, padx=10)
        
        # Next step button
        self.next_images_btn = tk.Button(
            analysis_buttons,
            text="Next: Images →",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.go_to_images,
            height=2,
            width=15,
            state="disabled"
        )
        self.next_images_btn.grid(row=0, column=3, padx=10)
        
    def on_drop(self, event, index):
        file_path = event.data.strip('{}')
        if file_path.lower().endswith('.mp3'):
            self.set_file_path(file_path, index)
        else:
            messagebox.showerror("Error", "Please select an MP3 file")
            
    def browse_file(self, index):
        file_path = filedialog.askopenfilename(
            title="Select MP3 file",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        if file_path:
            self.set_file_path(file_path, index)
            
    def set_file_path(self, file_path, index):
        if index == 0:
            self.original_file = file_path
            self.original_file_label.config(text=f"File: {os.path.basename(file_path)}")
        elif index == 1:
            self.instrumental_file = file_path
            self.instrumental_file_label.config(text=f"File: {os.path.basename(file_path)}")
        else:
            self.vocal_file = file_path
            self.vocal_file_label.config(text=f"File: {os.path.basename(file_path)}")
            
        # Update process button state
        self.update_process_button()
        
    def browse_analysis_file(self):
        """Browse for audio file to analyze"""
        file_path = filedialog.askopenfilename(
            title="Select audio file for analysis",
            filetypes=[("Audio files", "*.mp3 *.wav *.flac"), ("All files", "*.*")]
        )
        if file_path:
            self.analysis_file_var.set(f"Selected: {os.path.basename(file_path)}")
            self.analysis_file_path = file_path
            
    def use_processed_file(self):
        """Use the processed audio file for analysis"""
        if self.output_file and os.path.exists(self.output_file):
            self.analysis_file_path = self.output_file
            self.analysis_file_var.set(f"Using processed: {os.path.basename(self.output_file)}")
        else:
            messagebox.showwarning("Warning", "No processed file available. Please process audio first.")
        
    def update_process_button(self):
        if self.original_file and self.instrumental_file and self.vocal_file:
            self.process_btn.config(state="normal", bg="#4CAF50")
        else:
            self.process_btn.config(state="disabled", bg="#666666")
            
    def process_audio(self):
        if not all([self.original_file, self.instrumental_file, self.vocal_file]):
            messagebox.showerror("Error", "Please select all three audio files")
            return
            
        if not AUDIO_LIBS_AVAILABLE:
            messagebox.showerror("Error", 
                "Audio processing libraries are not installed.\n\n" +
                "Please run 'install_dependencies.bat' as Administrator first.")
            return
            
        # Choose output location
        output_path = filedialog.asksaveasfilename(
            title="Save processed audio as...",
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("WAV files", "*.wav")]
        )
        
        if not output_path:
            return
            
        self.output_file = output_path
        
        # Disable button and start processing
        self.process_btn.config(state="disabled", bg="#666666")
        self.progress_bar.start()
        self.progress_label.config(text="Processing audio...")
        
        # Run processing in separate thread
        threading.Thread(target=self.audio_processing_thread, daemon=True).start()
        
    def audio_processing_thread(self):
        try:
            processor = AudioProcessor()
            
            # Update progress
            self.root.after(0, lambda: self.progress_label.config(text="Loading audio files..."))
            
            # Load audio files
            original, sr1 = librosa.load(self.original_file, sr=44100)
            instrumental, sr2 = librosa.load(self.instrumental_file, sr=44100)
            vocal, sr3 = librosa.load(self.vocal_file, sr=44100)
            
            self.root.after(0, lambda: self.progress_label.config(text="Aligning vocal track..."))
            
            # Align vocal to original reference
            aligned_vocal = processor.align_audio(original, vocal)
            
            self.root.after(0, lambda: self.progress_label.config(text="Mixing audio..."))
            
            # Mix instrumental with aligned vocal
            final_audio = processor.mix_audio(instrumental, aligned_vocal)
            
            self.root.after(0, lambda: self.progress_label.config(text="Saving output..."))
            
            # Save output
            sf.write(self.output_file, final_audio, 44100)
            
            # Update UI on success
            self.root.after(0, self.processing_complete)
            
        except Exception as e:
            error_msg = f"Error processing audio: {str(e)}"
            self.root.after(0, lambda: self.processing_error(error_msg))
            
        
    def processing_error(self, error_msg):
        self.progress_bar.stop()
        self.progress_label.config(text="Processing failed")
        self.process_btn.config(state="normal", bg="#4CAF50")
        
        messagebox.showerror("Error", error_msg)
        
    def analyze_music(self):
        """Quick analyze button from audio processing tab"""
        if self.output_file and os.path.exists(self.output_file):
            self.analysis_file_path = self.output_file
            self.analysis_file_var.set(f"Using processed: {os.path.basename(self.output_file)}")
            self.notebook.select(self.analysis_tab)  # Switch to analysis tab
            self.run_music_analysis()
        elif self.original_file:
            self.analysis_file_path = self.original_file
            self.analysis_file_var.set(f"Using original: {os.path.basename(self.original_file)}")
            self.notebook.select(self.analysis_tab)  # Switch to analysis tab
            self.run_music_analysis()
        else:
            messagebox.showwarning("Warning", "Please select an audio file first.")
            
    def run_music_analysis(self):
        """Run comprehensive music analysis"""
        if not hasattr(self, 'analysis_file_path') or not self.analysis_file_path:
            messagebox.showerror("Error", "Please select an audio file to analyze first.")
            return
            
        if not AUDIO_LIBS_AVAILABLE:
            messagebox.showerror("Error", 
                "Audio processing libraries are not installed.\n\n" +
                "Please run 'install_dependencies.bat' as Administrator first.")
            return
            
        # Show progress in JSON display
        self.json_display.config(state="normal")
        self.json_display.delete("1.0", tk.END)
        self.json_display.insert(tk.END, "Analyzing audio... Please wait...\n")
        self.json_display.config(state="disabled")
        
        # Run analysis in separate thread
        threading.Thread(target=self.music_analysis_thread, daemon=True).start()
        
    def music_analysis_thread(self):
        """Perform music analysis in background thread"""
        try:
            analyzer = MusicAnalyzer()
            
            # Update display
            def update_status(status):
                self.json_display.config(state="normal")
                self.json_display.delete("1.0", tk.END)
                self.json_display.insert(tk.END, f"Analyzing audio... {status}\n")
                self.json_display.config(state="disabled")
            
            self.root.after(0, lambda: update_status("Loading audio file..."))
            
            # Perform analysis
            analysis_result = analyzer.analyze_audio_file(self.analysis_file_path)
            
            self.root.after(0, lambda: update_status("Processing results..."))
            
            # Convert to our JSON format
            self.music_analysis = analysis_result
            self.analysis_json = self.create_analysis_json(analysis_result, self.analysis_file_path)
            
            # Update display with results
            self.root.after(0, self.display_analysis_results)
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.root.after(0, lambda: self.analysis_error(error_msg))
            
    def display_analysis_results(self):
        """Display analysis results in JSON format"""
        if self.analysis_json:
            formatted_json = json.dumps(self.analysis_json, indent=2)
            
            self.json_display.config(state="normal")
            self.json_display.delete("1.0", tk.END)
            self.json_display.insert(tk.END, formatted_json)
            self.json_display.config(state="disabled")
            
            # Enable export button
            self.export_json_btn.config(state="normal", bg="#9C27B0")
            
            # Enable next step button
            self.next_images_btn.config(state="normal", bg="#4CAF50")
            
            # Enable image search and LLM test buttons
            self.search_images_btn.config(state="normal", bg="#FF9800")
            self.test_llm_btn.config(state="normal", bg="#9E9E9E")
            
            messagebox.showinfo("Success", "Music analysis completed successfully!")
        
    def analysis_error(self, error_msg):
        """Handle analysis error"""
        self.json_display.config(state="normal")
        self.json_display.delete("1.0", tk.END)
        self.json_display.insert(tk.END, f"Analysis Error:\n{error_msg}")
        self.json_display.config(state="disabled")
        
        messagebox.showerror("Analysis Error", error_msg)
        
    def export_analysis_json(self):
        """Export analysis results to JSON file"""
        if not self.analysis_json:
            messagebox.showwarning("Warning", "No analysis data to export.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Export analysis as JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.analysis_json, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Success", f"Analysis exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export JSON:\n{str(e)}")
                
    def clear_analysis(self):
        """Clear analysis results"""
        self.json_display.config(state="normal")
        self.json_display.delete("1.0", tk.END)
        self.json_display.insert(tk.END, "Analysis cleared. Ready for new analysis.")
        self.json_display.config(state="disabled")
        
        self.music_analysis = None
        self.analysis_json = None
        self.export_json_btn.config(state="disabled", bg="#666666")
        
    def create_analysis_json(self, analysis_result, file_path):
        """Convert analysis result to simplified JSON format for LLM image selection"""
        return {
            "song": os.path.basename(file_path),
            "duration": round(analysis_result.get('duration', 0), 1),
            "overall_mood": {
                "energy": round(analysis_result.get('energy', 0.5), 2),
                "vibe": self.get_overall_vibe(analysis_result.get('energy', 0.5), analysis_result.get('valence', 0.5)),
                "tempo": round(analysis_result.get('tempo', 120)),
                "key": analysis_result.get('key', 'C')
            },
            "video_sections": self.format_simple_sections(analysis_result.get('sections', []))
        }
        
    def format_simple_sections(self, sections):
        """Format sections for simplified LLM processing"""
        simple_sections = []
        for i, section in enumerate(sections):
            simple_section = {
                "start": round(section.get('start_time', 0), 1),
                "end": round(section.get('end_time', 0), 1),
                "type": section.get('type', 'verse'),
                "energy": round(section.get('energy', 0.5), 2),
                "mood": self.get_simple_mood(section.get('energy', 0.5), section.get('valence', 0.5)),
                "colors": self.get_color_palette(section.get('valence', 0.5), section.get('energy', 0.5))
            }
            simple_sections.append(simple_section)
        return simple_sections
        
    def get_overall_vibe(self, energy, valence):
        """Get overall song vibe for LLM"""
        if energy > 0.7 and valence > 0.6:
            return "energetic_happy"
        elif energy > 0.7 and valence < 0.4:
            return "intense_dramatic"
        elif energy < 0.3 and valence > 0.6:
            return "calm_peaceful" 
        elif energy < 0.3 and valence < 0.4:
            return "melancholic_ambient"
        elif valence > 0.6:
            return "upbeat_positive"
        elif valence < 0.4:
            return "sad_emotional"
        else:
            return "balanced_neutral"
            
    def get_simple_mood(self, energy, valence):
        """Get simple mood descriptor for section"""
        if energy > 0.6:
            return "high" if valence > 0.5 else "intense"
        elif energy > 0.4:
            return "medium" if valence > 0.5 else "dramatic"
        else:
            return "calm" if valence > 0.5 else "dark"
            
    def get_color_palette(self, valence, energy):
        """Generate simple color palette for image search"""
        if valence > 0.6 and energy > 0.6:
            return ["warm", "bright", "energetic"]
        elif valence > 0.6:
            return ["soft", "light", "peaceful"]
        elif valence < 0.4 and energy < 0.4:
            return ["dark", "moody", "atmospheric"]
        elif valence < 0.4:
            return ["intense", "dramatic", "bold"]
        else:
            return ["neutral", "balanced", "natural"]
            
    def processing_complete(self):
        self.progress_bar.stop()
        self.progress_label.config(text="Processing complete!")
        self.output_path_label.config(text=f"Saved: {self.output_file}")
        self.process_btn.config(state="normal", bg="#4CAF50")
        
        # Enable use processed file button
        self.use_processed_btn.config(state="normal", bg="#555555")
        
        # Enable next step button
        self.next_analysis_btn.config(state="normal", bg="#9C27B0")
        
        messagebox.showinfo("Success", f"Audio processed successfully!\n\nOutput saved to:\n{self.output_file}")

    def setup_image_tab(self):
        """Setup the image management tab"""
        self.image_tab.grid_rowconfigure(1, weight=1)
        self.image_tab.grid_columnconfigure(0, weight=1)
        
        # Title
        title_frame = tk.Frame(self.image_tab, bg="#2b2b2b")
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(
            title_frame,
            text="Image Management & Download",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#2b2b2b"
        )
        title_label.grid(row=0, column=0)
        
        instructions = tk.Label(
            title_frame,
            text="Download mood-based images for each music section using Unsplash API",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#2b2b2b"
        )
        instructions.grid(row=1, column=0, pady=5)
        
        # Main content area
        content_frame = tk.Frame(self.image_tab, bg="#2b2b2b")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_rowconfigure(2, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # API Key section
        api_frame = tk.Frame(content_frame, bg="#3b3b3b", relief="raised", bd=2)
        api_frame.grid(row=0, column=0, sticky="ew", pady=10)
        api_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            api_frame,
            text="Unsplash API Key:",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Load API key from .env file
        api_key_from_env = ""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('UNSPLASH_API='):
                        api_key_from_env = line.split('=', 1)[1].strip().strip('"')
                        break
        except:
            pass
        
        self.api_key_var = tk.StringVar(value=api_key_from_env or os.getenv('UNSPLASH_ACCESS_KEY', ''))
        self.api_key_entry = tk.Entry(
            api_frame,
            textvariable=self.api_key_var,
            font=("Arial", 10),
            show="*",
            width=50
        )
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        tk.Button(
            api_frame,
            text="Get Free API Key",
            font=("Arial", 9),
            bg="#555555",
            fg="white",
            command=self.open_unsplash_signup,
            width=15
        ).grid(row=0, column=2, padx=10, pady=10)
        
        # LLM Settings section
        llm_frame = tk.Frame(content_frame, bg="#3b3b3b", relief="raised", bd=2)
        llm_frame.grid(row=1, column=0, sticky="ew", pady=10)
        llm_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            llm_frame,
            text="LLM Integration (LMStudio):",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.llm_url_var = tk.StringVar(value="http://localhost:1234")
        llm_url_entry = tk.Entry(
            llm_frame,
            textvariable=self.llm_url_var,
            font=("Arial", 10),
            width=30
        )
        llm_url_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.test_llm_btn = tk.Button(
            llm_frame,
            text="Test LLM",
            font=("Arial", 9),
            bg="#555555",
            fg="white",
            command=self.test_llm_connection,
            width=12
        )
        self.test_llm_btn.grid(row=0, column=2, padx=10, pady=10)
        
        self.llm_status_label = tk.Label(
            llm_frame,
            text="LLM Status: Not tested",
            font=("Arial", 9),
            fg="#cccccc",
            bg="#3b3b3b"
        )
        self.llm_status_label.grid(row=1, column=0, columnspan=3, padx=20, pady=5, sticky="w")
        
        # Settings section
        settings_frame = tk.Frame(content_frame, bg="#3b3b3b", relief="raised", bd=2)
        settings_frame.grid(row=2, column=0, sticky="ew", pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            settings_frame,
            text="Images per Section:",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.images_per_section_var = tk.IntVar(value=1)
        images_spinbox = tk.Spinbox(
            settings_frame,
            from_=1, to=10,
            textvariable=self.images_per_section_var,
            font=("Arial", 10),
            width=5
        )
        images_spinbox.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Status and results area
        results_frame = tk.Frame(content_frame, bg="#2b2b2b")
        results_frame.grid(row=3, column=0, sticky="nsew", pady=10)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Status display
        self.image_status_display = scrolledtext.ScrolledText(
            results_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD,
            state="disabled",
            height=15
        )
        self.image_status_display.grid(row=0, column=0, sticky="nsew")
        
        # Control buttons
        button_frame = tk.Frame(content_frame, bg="#2b2b2b")
        button_frame.grid(row=4, column=0, pady=20)
        
        self.search_images_btn = tk.Button(
            button_frame,
            text="Search Images",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            command=self.search_images,
            height=2,
            width=15,
            state="disabled"
        )
        self.search_images_btn.grid(row=0, column=0, padx=10)
        
        self.test_llm_btn = tk.Button(
            button_frame,
            text="Test LLM Only",
            font=("Arial", 10, "bold"),
            bg="#9E9E9E",
            fg="white",
            command=self.test_llm_search,
            height=1,
            width=15,
            state="disabled"
        )
        self.test_llm_btn.grid(row=1, column=0, padx=10, pady=5)
        
        self.download_images_btn = tk.Button(
            button_frame,
            text="Download Images",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.download_images,
            height=2,
            width=15,
            state="disabled"
        )
        self.download_images_btn.grid(row=0, column=1, padx=10)
        
        self.process_images_btn = tk.Button(
            button_frame,
            text="Process for Video",
            font=("Arial", 12, "bold"),
            bg="#9C27B0",
            fg="white",
            command=self.process_images,
            height=2,
            width=15,
            state="disabled"
        )
        self.process_images_btn.grid(row=0, column=2, padx=10)
        
        tk.Button(
            button_frame,
            text="Clear Results",
            font=("Arial", 12, "bold"),
            bg="#F44336",
            fg="white",
            command=self.clear_image_results,
            height=2,
            width=15
        ).grid(row=0, column=3, padx=10)
        
        # Next step button
        self.next_video_btn = tk.Button(
            button_frame,
            text="Next: Video →",
            font=("Arial", 12, "bold"),
            bg="#673AB7",
            fg="white",
            command=self.go_to_video,
            height=2,
            width=15,
            state="disabled"
        )
        self.next_video_btn.grid(row=1, column=2, columnspan=2, padx=10, pady=5)
    
    def open_unsplash_signup(self):
        """Open Unsplash developer signup page"""
        import webbrowser
        webbrowser.open("https://unsplash.com/developers")
    
    def test_llm_connection(self):
        """Test connection to local LLM (LMStudio)"""
        llm_url = self.llm_url_var.get().strip()
        
        try:
            self.llm_manager = LocalLLMManager(base_url=llm_url)
            if self.llm_manager.test_connection():
                self.llm_status_label.config(text="LLM Status: ✓ Connected", fg="#4CAF50")
                messagebox.showinfo("Success", "LLM connection successful!\nIntelligent image selection enabled.")
            else:
                self.llm_status_label.config(text="LLM Status: ✗ Connection failed", fg="#F44336")
                messagebox.showerror("Error", "Cannot connect to LMStudio.\nPlease ensure LMStudio is running and a model is loaded.")
        except Exception as e:
            self.llm_status_label.config(text="LLM Status: ✗ Error", fg="#F44336")
            messagebox.showerror("Error", f"LLM connection error: {str(e)}")
    
    def update_image_status(self, message):
        """Update image status display"""
        self.image_status_display.config(state="normal")
        self.image_status_display.insert(tk.END, f"{message}\n")
        self.image_status_display.see(tk.END)
        self.image_status_display.config(state="disabled")
        self.root.update()
    
    def test_llm_search(self):
        """Test LLM connection and show image search queries in log"""
        if not self.analysis_json:
            messagebox.showerror("Error", "Please complete music analysis first.")
            return
        
        if not self.llm_manager:
            messagebox.showerror("Error", "Please test LLM connection first.")
            return
        
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Unsplash API key.")
            return
        
        # Disable button and clear status
        self.search_images_btn.config(state="disabled", bg="#666666")
        self.image_status_display.config(state="normal")
        self.image_status_display.delete("1.0", tk.END)
        self.image_status_display.config(state="disabled")
        
        # Run test in separate thread
        threading.Thread(target=self.test_llm_search_thread, args=(api_key,), daemon=True).start()
    
    def search_images(self):
        """Search for images based on music analysis"""
        if not self.analysis_json:
            messagebox.showerror("Error", "Please complete music analysis first.")
            return
        
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter your Unsplash API key.")
            return
        
        # Disable button and clear status
        self.search_images_btn.config(state="disabled", bg="#666666")
        self.image_status_display.config(state="normal")
        self.image_status_display.delete("1.0", tk.END)
        self.image_status_display.config(state="disabled")
        
        # Run search in separate thread
        threading.Thread(target=self.search_images_thread, args=(api_key,), daemon=True).start()
    
    def test_llm_search_thread(self, api_key):
        """Test LLM image search and display detailed output in log"""
        try:
            # Initialize image manager
            self.image_manager = UnsplashImageManager(api_key)
            
            self.root.after(0, lambda: self.update_image_status("=== LLM INTEGRATION TEST ==="))
            self.root.after(0, lambda: self.update_image_status("Testing LMStudio connection..."))
            
            # Test LLM connection
            if not self.llm_manager.test_connection():
                self.root.after(0, lambda: self.update_image_status("ERROR: LMStudio not accessible!"))
                self.root.after(0, lambda: self.update_image_status("Please ensure LMStudio is running and a model is loaded."))
                return
            
            self.root.after(0, lambda: self.update_image_status("✓ LMStudio connection successful"))
            self.root.after(0, lambda: self.update_image_status(""))
            
            # Show input music analysis
            self.root.after(0, lambda: self.update_image_status("INPUT MUSIC ANALYSIS:"))
            self.root.after(0, lambda: self.update_image_status("-" * 40))
            self.root.after(0, lambda: self.update_image_status(f"Song: {self.analysis_json.get('song', 'Unknown')}"))
            self.root.after(0, lambda: self.update_image_status(f"Duration: {self.analysis_json.get('duration', 0):.1f}s"))
            
            overall_mood = self.analysis_json.get('overall_mood', {})
            self.root.after(0, lambda: self.update_image_status(f"Energy: {overall_mood.get('energy', 0)}"))
            self.root.after(0, lambda: self.update_image_status(f"Vibe: {overall_mood.get('vibe', 'neutral')}"))
            self.root.after(0, lambda: self.update_image_status(f"Tempo: {overall_mood.get('tempo', 120)} BPM"))
            self.root.after(0, lambda: self.update_image_status(""))
            
            # Show sections
            sections = self.analysis_json.get('video_sections', [])
            for i, section in enumerate(sections):
                self.root.after(0, lambda s=section, i=i: self.update_image_status(
                    f"Section {i+1}: {s.get('type', 'verse')} ({s.get('start', 0):.1f}s-{s.get('end', 0):.1f}s) "
                    f"Energy: {s.get('energy', 0)} Mood: {s.get('mood', 'neutral')} Colors: {s.get('colors', [])}"
                ))
            
            self.root.after(0, lambda: self.update_image_status(""))
            self.root.after(0, lambda: self.update_image_status("CALLING LLM FOR INTELLIGENT IMAGE QUERIES..."))
            self.root.after(0, lambda: self.update_image_status("-" * 50))
            
            # Generate LLM queries
            self.enhanced_image_manager = EnhancedImageManager(self.image_manager, self.llm_manager)
            llm_queries = self.llm_manager.generate_image_queries(self.analysis_json)
            
            # Display LLM output in detail
            self.root.after(0, lambda: self.update_image_status("LLM GENERATED IMAGE SEARCH QUERIES:"))
            self.root.after(0, lambda: self.update_image_status("=" * 50))
            
            for section_key, query in llm_queries.items():
                section_num = section_key.split('_')[1]
                self.root.after(0, lambda s=section_num, q=query: self.update_image_status(f"\nSECTION {int(s)+1}:"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  Primary Keywords: {', '.join(q.primary_keywords)}"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  Style Keywords: {', '.join(q.style_keywords)}"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  Mood Keywords: {', '.join(q.mood_keywords)}"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  Exclude Keywords: {', '.join(q.exclude_keywords)}"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  Orientation: {q.orientation}"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  Color Filter: {q.color}"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  Order: {q.order_by}"))
                self.root.after(0, lambda q=query: self.update_image_status(f"  → Unsplash Query: \"{q.to_unsplash_query()}\""))
            
            # Test search API calls (without downloading)
            self.root.after(0, lambda: self.update_image_status(""))
            self.root.after(0, lambda: self.update_image_status("TESTING UNSPLASH API CALLS:"))
            self.root.after(0, lambda: self.update_image_status("-" * 40))
            
            for section_key, query in llm_queries.items():
                section_num = section_key.split('_')[1]
                self.root.after(0, lambda s=section_num: self.update_image_status(f"\nTesting search for Section {int(s)+1}..."))
                
                # Simulate search (just test the API call)
                images = self.enhanced_image_manager.search_with_enhanced_query(query, count=3)
                
                self.root.after(0, lambda s=section_num, c=len(images): 
                    self.update_image_status(f"Section {int(s)+1}: Found {c} images"))
                
                # Show first few image results
                for i, img in enumerate(images[:2]):
                    self.root.after(0, lambda i=i, img=img: 
                        self.update_image_status(f"  Image {i+1}: {img.description[:50]}... (by {img.photographer})"))
                
                import time
                time.sleep(0.5)  # Rate limiting
            
            self.root.after(0, lambda: self.update_image_status(""))
            self.root.after(0, lambda: self.update_image_status("=== TEST COMPLETED SUCCESSFULLY! ==="))
            self.root.after(0, lambda: self.update_image_status("LLM is working correctly and generating intelligent image queries."))
            
        except Exception as e:
            error_msg = f"LLM Test failed: {str(e)}"
            self.root.after(0, lambda: self.update_image_status(f"ERROR: {error_msg}"))
            import traceback
            self.root.after(0, lambda: self.update_image_status(f"Traceback: {traceback.format_exc()}"))
        finally:
            self.root.after(0, lambda: self.search_images_btn.config(state="normal", bg="#FF9800"))
    
    def search_images_thread(self, api_key):
        """Search for images in background thread using LLM intelligence"""
        try:
            # Initialize image manager
            self.image_manager = UnsplashImageManager(api_key)
            
            self.root.after(0, lambda: self.update_image_status("Initializing image search..."))
            
            images_per_section = self.images_per_section_var.get()
            
            # Check if LLM is available for intelligent search
            if self.llm_manager and self.llm_manager.test_connection():
                self.root.after(0, lambda: self.update_image_status("🧠 Using LLM for intelligent image selection..."))
                
                # Initialize enhanced image manager with LLM
                self.enhanced_image_manager = EnhancedImageManager(self.image_manager, self.llm_manager)
                
                # Use LLM-powered intelligent search
                self.sections_images = self.enhanced_image_manager.search_intelligent_images(
                    self.analysis_json,
                    images_per_section=images_per_section
                )
                
                self.root.after(0, lambda: self.update_image_status("✨ LLM-powered image search completed!"))
                
            else:
                # Fallback to basic search
                self.root.after(0, lambda: self.update_image_status("Using basic image search (LLM not connected)..."))
                
                self.sections_images = self.image_manager.process_music_analysis(
                    self.analysis_json, 
                    images_per_section=images_per_section
                )
            
            # Update status with results
            total_images = sum(len(images) for images in self.sections_images.values())
            self.root.after(0, lambda: self.update_image_status(f"Found {total_images} images across {len(self.sections_images)} sections"))
            
            for section_key, images in self.sections_images.items():
                section_num = section_key.split('_')[1]
                self.root.after(0, lambda s=section_num, c=len(images): 
                    self.update_image_status(f"Section {int(s)+1}: {c} images found"))
            
            # Enable download button
            self.root.after(0, lambda: self.download_images_btn.config(state="normal", bg="#4CAF50"))
            self.root.after(0, lambda: self.update_image_status("Ready to download images!"))
            
        except Exception as e:
            error_msg = f"Image search failed: {str(e)}"
            self.root.after(0, lambda: self.update_image_status(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, lambda: self.search_images_btn.config(state="normal", bg="#FF9800"))
    
    def download_images(self):
        """Download all found images"""
        if not self.sections_images:
            messagebox.showerror("Error", "Please search for images first.")
            return
        
        # Disable button
        self.download_images_btn.config(state="disabled", bg="#666666")
        
        # Run download in separate thread
        threading.Thread(target=self.download_images_thread, daemon=True).start()
    
    def download_images_thread(self):
        """Download images in background thread"""
        try:
            self.root.after(0, lambda: self.update_image_status("Starting image downloads..."))
            
            # Download all section images
            self.downloaded_paths = self.image_manager.download_section_images(self.sections_images)
            
            # Update status
            total_downloaded = sum(len(paths) for paths in self.downloaded_paths.values())
            self.root.after(0, lambda: self.update_image_status(f"Downloaded {total_downloaded} images successfully!"))
            
            for section_key, paths in self.downloaded_paths.items():
                section_num = section_key.split('_')[1]
                self.root.after(0, lambda s=section_num, c=len(paths): 
                    self.update_image_status(f"Section {int(s)+1}: {c} images downloaded"))
            
            # Enable process button
            self.root.after(0, lambda: self.process_images_btn.config(state="normal", bg="#9C27B0"))
            self.root.after(0, lambda: self.update_image_status("Ready to process images for video!"))
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.root.after(0, lambda: self.update_image_status(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, lambda: self.download_images_btn.config(state="normal", bg="#4CAF50"))
    
    def process_images(self):
        """Process downloaded images for video compatibility"""
        if not self.downloaded_paths:
            messagebox.showerror("Error", "Please download images first.")
            return
        
        # Disable button
        self.process_images_btn.config(state="disabled", bg="#666666")
        
        # Run processing in separate thread
        threading.Thread(target=self.process_images_thread, daemon=True).start()
    
    def process_images_thread(self):
        """Process images in background thread"""
        try:
            self.root.after(0, lambda: self.update_image_status("Processing images for video compatibility..."))
            
            processed_count = 0
            
            for section_key, image_paths in self.downloaded_paths.items():
                if image_paths:
                    section_dir = os.path.join("processed_images", section_key)
                    processed_paths = ImageProcessor.process_section_images(image_paths, section_dir)
                    
                    section_num = section_key.split('_')[1]
                    self.root.after(0, lambda s=section_num, c=len(processed_paths): 
                        self.update_image_status(f"Section {int(s)+1}: {c} images processed"))
                    
                    processed_count += len(processed_paths)
            
            self.root.after(0, lambda: self.update_image_status(f"Processing complete! {processed_count} images ready for video."))
            
            # Skip cleanup to preserve images for reuse (API limits)
            self.root.after(0, lambda: self.update_image_status("💾 Preserving original images for reuse (API limits)."))
            
            # Enable next step button
            self.root.after(0, lambda: self.next_video_btn.config(state="normal", bg="#673AB7"))
            
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Image processing completed!\n{processed_count} images processed for video compatibility.\n\nOriginal images preserved for reuse.\n\nReady for video generation!"))
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            self.root.after(0, lambda: self.update_image_status(error_msg))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, lambda: self.process_images_btn.config(state="normal", bg="#9C27B0"))
    
    def go_to_analysis(self):
        """Navigate to analysis tab"""
        self.notebook.select(self.analysis_tab)
    
    def go_to_images(self):
        """Navigate to image management tab"""
        self.notebook.select(self.image_tab)
    
    def go_to_video(self):
        """Navigate to video generation tab"""
        self.notebook.select(self.video_tab)
    
    def setup_video_tab(self):
        """Setup the video generation tab"""
        self.video_tab.grid_rowconfigure(1, weight=1)
        self.video_tab.grid_columnconfigure(0, weight=1)
        
        # Title
        title_frame = tk.Frame(self.video_tab, bg="#2b2b2b")
        title_frame.grid(row=0, column=0, sticky="ew", pady=10)
        title_frame.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(
            title_frame,
            text="Video Generation & Export",
            font=("Arial", 18, "bold"),
            fg="white",
            bg="#2b2b2b"
        )
        title_label.grid(row=0, column=0)
        
        instructions = tk.Label(
            title_frame,
            text="Generate music video by syncing processed images with audio sections",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#2b2b2b"
        )
        instructions.grid(row=1, column=0, pady=5)
        
        # Main content area
        content_frame = tk.Frame(self.video_tab, bg="#2b2b2b")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_rowconfigure(2, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Video settings section
        settings_frame = tk.Frame(content_frame, bg="#3b3b3b", relief="raised", bd=2)
        settings_frame.grid(row=0, column=0, sticky="ew", pady=10)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            settings_frame,
            text="Video Settings:",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=0, column=0, columnspan=3, padx=20, pady=10, sticky="w")
        
        # Resolution setting
        tk.Label(
            settings_frame,
            text="Resolution:",
            font=("Arial", 10),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.resolution_var = tk.StringVar(value="1920x1080")
        resolution_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.resolution_var,
            values=["1920x1080", "1280x720", "3840x2160"],
            state="readonly",
            width=15
        )
        resolution_combo.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # FPS setting
        tk.Label(
            settings_frame,
            text="FPS:",
            font=("Arial", 10),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=1, column=2, padx=20, pady=5, sticky="w")
        
        self.fps_var = tk.IntVar(value=30)
        fps_spinbox = tk.Spinbox(
            settings_frame,
            from_=24, to=60,
            textvariable=self.fps_var,
            font=("Arial", 10),
            width=5
        )
        fps_spinbox.grid(row=1, column=3, padx=10, pady=5, sticky="w")
        
        # Transition setting
        tk.Label(
            settings_frame,
            text="Transition Duration:",
            font=("Arial", 10),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.transition_var = tk.DoubleVar(value=1.0)
        transition_spinbox = tk.Spinbox(
            settings_frame,
            from_=0.5, to=3.0, increment=0.1,
            textvariable=self.transition_var,
            font=("Arial", 10),
            width=8
        )
        transition_spinbox.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        tk.Label(
            settings_frame,
            text="seconds",
            font=("Arial", 9),
            fg="#cccccc",
            bg="#3b3b3b"
        ).grid(row=2, column=2, padx=5, pady=5, sticky="w")
        
        # Video effects section
        tk.Label(
            settings_frame,
            text="Video Effects:",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=3, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.use_fade_transitions = tk.BooleanVar(value=True)
        fade_check = tk.Checkbutton(
            settings_frame,
            text="Fade transitions between sections",
            variable=self.use_fade_transitions,
            font=("Arial", 10),
            fg="white",
            bg="#3b3b3b",
            selectcolor="#4CAF50"
        )
        fade_check.grid(row=4, column=0, columnspan=2, padx=40, pady=2, sticky="w")
        
        self.add_visualizer = tk.BooleanVar(value=True)
        visualizer_check = tk.Checkbutton(
            settings_frame,
            text="Professional blue audio visualizer",
            variable=self.add_visualizer,
            font=("Arial", 10),
            fg="white",
            bg="#3b3b3b",
            selectcolor="#4CAF50"
        )
        visualizer_check.grid(row=5, column=0, columnspan=2, padx=40, pady=2, sticky="w")
        
        # Set default visualizer style (no user selection needed)
        self.visualizer_style = tk.StringVar(value="professional_blue")
        
        # Input validation section
        validation_frame = tk.Frame(content_frame, bg="#3b3b3b", relief="raised", bd=2)
        validation_frame.grid(row=1, column=0, sticky="ew", pady=10)
        validation_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(
            validation_frame,
            text="Input Validation:",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#3b3b3b"
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        
        self.validation_status = tk.Text(
            validation_frame,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            height=6,
            wrap=tk.WORD
        )
        self.validation_status.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        
        tk.Button(
            validation_frame,
            text="Validate Inputs",
            font=("Arial", 10, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.validate_video_inputs,
            width=15
        ).grid(row=2, column=0, padx=20, pady=10)
        
        # Status and results area
        results_frame = tk.Frame(content_frame, bg="#2b2b2b")
        results_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        progress_frame = tk.Frame(results_frame, bg="#2b2b2b")
        progress_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Ready to generate video",
            font=("Arial", 10),
            fg="#cccccc",
            bg="#2b2b2b"
        )
        self.progress_label.grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=400,
            style='TProgressbar'
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        
        # Video generation status display
        self.video_status_display = scrolledtext.ScrolledText(
            results_frame,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD,
            state="disabled",
            height=12
        )
        self.video_status_display.grid(row=1, column=0, sticky="nsew")
        
        # Control buttons for video generation
        video_buttons = tk.Frame(content_frame, bg="#2b2b2b")
        video_buttons.grid(row=3, column=0, pady=20)
        
        self.generate_video_btn = tk.Button(
            video_buttons,
            text="Generate Video",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.generate_video,
            height=2,
            width=15,
            state="disabled"
        )
        self.generate_video_btn.grid(row=0, column=0, padx=10)
        
        tk.Button(
            video_buttons,
            text="Open Output Folder",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            command=self.open_output_folder,
            height=2,
            width=15
        ).grid(row=0, column=1, padx=10)
        
        tk.Button(
            video_buttons,
            text="Clear Results",
            font=("Arial", 12, "bold"),
            bg="#F44336",
            fg="white",
            command=self.clear_video_results,
            height=2,
            width=15
        ).grid(row=0, column=2, padx=10)
    
    def cleanup_section_images(self):
        """Clean up original downloaded images after processing to save space"""
        import shutil
        
        if not self.downloaded_paths:
            return
        
        try:
            cleaned_count = 0
            for section_key, image_paths in self.downloaded_paths.items():
                section_dir = os.path.join("section_images", section_key)
                if os.path.exists(section_dir):
                    # Count files before deletion
                    files_in_dir = len([f for f in os.listdir(section_dir) if os.path.isfile(os.path.join(section_dir, f))])
                    cleaned_count += files_in_dir
                    
                    # Remove the entire section directory
                    shutil.rmtree(section_dir)
            
            print(f"Cleaned up {cleaned_count} original image files to save space")
            
        except Exception as e:
            print(f"Cleanup error (non-critical): {e}")
    
    def clear_image_results(self):
        """Clear image search and download results"""
        self.image_status_display.config(state="normal")
        self.image_status_display.delete("1.0", tk.END)
        self.image_status_display.insert(tk.END, "Image results cleared. Ready for new search.\n")
        self.image_status_display.config(state="disabled")
        
        self.sections_images = None
        self.downloaded_paths = None
        self.download_images_btn.config(state="disabled", bg="#666666")
        self.process_images_btn.config(state="disabled", bg="#666666")
    
    def validate_video_inputs(self):
        """Validate inputs for video generation"""
        self.validation_status.delete("1.0", tk.END)
        
        if not self.analysis_json:
            self.validation_status.insert(tk.END, "❌ Music analysis data missing\n")
        else:
            self.validation_status.insert(tk.END, "✓ Music analysis data available\n")
        
        # Check for audio file from either processing or analysis tab
        audio_file = self.output_file or getattr(self, 'analysis_file_path', None)
        
        if not audio_file or not os.path.exists(audio_file):
            self.validation_status.insert(tk.END, "❌ Audio file missing (need processed or analysis file)\n")
        else:
            source = "processed" if self.output_file else "analysis"
            self.validation_status.insert(tk.END, f"✓ Audio file ({source}): {os.path.basename(audio_file)}\n")
        
        # Check for processed images (they are in section_images)
        processed_images_dir = "section_images"  
        
        # Check if we have audio file from analysis tab
        audio_file_path = self.output_file or getattr(self, 'analysis_file_path', None)
        if not audio_file_path and hasattr(self, 'analysis_file_path'):
            audio_file_path = self.analysis_file_path
        
        errors = VideoGeneratorGUI.validate_inputs(self.analysis_json, processed_images_dir, audio_file_path or "")
        
        if errors:
            for error in errors:
                self.validation_status.insert(tk.END, f"❌ {error}\n")
        else:
            self.validation_status.insert(tk.END, "✓ All validation checks passed!\n")
            self.generate_video_btn.config(state="normal", bg="#4CAF50")
        
        # Show sections info
        if self.analysis_json:
            sections = self.analysis_json.get('video_sections', [])
            self.validation_status.insert(tk.END, f"\n📊 Found {len(sections)} music sections:\n")
            for i, section in enumerate(sections):
                section_type = section.get('type', 'unknown')
                start = section.get('start', 0)
                end = section.get('end', 0)
                self.validation_status.insert(tk.END, f"  {i+1}. {section_type} ({start:.1f}s-{end:.1f}s)\n")
    
    def update_video_status(self, message):
        """Update video status display"""
        self.video_status_display.config(state="normal")
        self.video_status_display.insert(tk.END, f"{message}\n")
        self.video_status_display.see(tk.END)
        self.video_status_display.config(state="disabled")
        self.root.update()
    
    def generate_video(self):
        """Generate video from processed images and audio"""
        # Get audio file from either processing or analysis tab
        audio_file = self.output_file or getattr(self, 'analysis_file_path', None)
        
        if not self.analysis_json or not audio_file:
            messagebox.showerror("Error", "Please complete music analysis and have an audio file ready.")
            return
        
        # Choose output location
        output_path = filedialog.asksaveasfilename(
            title="Save video as...",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        
        if not output_path:
            return
        
        self.video_output_path = output_path
        
        # Disable button and start generation
        self.generate_video_btn.config(state="disabled", bg="#666666")
        self.video_status_display.config(state="normal")
        self.video_status_display.delete("1.0", tk.END)
        self.video_status_display.config(state="disabled")
        
        # Run generation in separate thread
        threading.Thread(target=self.generate_video_thread, daemon=True).start()
    
    def generate_video_thread(self):
        """Generate video in background thread"""
        try:
            # Parse resolution
            resolution = self.resolution_var.get()
            width, height = map(int, resolution.split('x'))
            fps = self.fps_var.get()
            transition_duration = self.transition_var.get()
            
            self.root.after(0, lambda: self.update_video_status("=== VIDEO GENERATION STARTED ==="))
            self.root.after(0, lambda: self.update_video_status(f"Settings: {resolution} @ {fps}fps, {transition_duration}s transitions"))
            
            # Initialize video generator
            self.video_generator = VideoGenerator(output_resolution=(width, height), fps=fps)
            
            self.root.after(0, lambda: self.update_video_status("✓ Video generator initialized"))
            self.root.after(0, lambda: self.update_video_status("📁 Finding processed images in section_images..."))
            
            # Get correct audio file
            audio_file = self.output_file or getattr(self, 'analysis_file_path', None)
            
            # Generate video with new options
            use_fade_transitions = self.use_fade_transitions.get()
            add_visualizer = self.add_visualizer.get()
            visualizer_style = self.visualizer_style.get()
            
            self.root.after(0, lambda: self.update_video_status(f"🎨 Video effects: Fade transitions={use_fade_transitions}, Visualizer={add_visualizer} ({visualizer_style})"))
            
            def progress_callback(message, progress):
                """Update progress bar and label from video generation"""
                self.root.after(0, lambda: self.progress_label.config(text=message))
                self.root.after(0, lambda: self.progress_bar.config(value=progress))
                self.root.after(0, lambda: self.update_video_status(f"[{progress}%] {message}"))
            
            final_path = self.video_generator.create_video_from_analysis(
                music_analysis=self.analysis_json,
                processed_images_dir="section_images",  # Correct directory
                audio_file=audio_file,
                output_path=self.video_output_path,
                transition_duration=transition_duration,
                progress_callback=progress_callback,
                add_visualizer=add_visualizer,
                use_fade_transitions=use_fade_transitions,
                visualizer_style=visualizer_style
            )
            
            self.root.after(0, lambda: self.update_video_status("🎬 Video rendering completed!"))
            self.root.after(0, lambda: self.update_video_status(f"✓ Video saved: {os.path.basename(final_path)}"))
            self.root.after(0, lambda: self.update_video_status("=== VIDEO GENERATION COMPLETE ==="))
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", 
                f"Video generated successfully!\n\nOutput: {final_path}\n\nYou can now open the output folder to view your music video."
            ))
            
        except Exception as e:
            error_msg = f"Video generation failed: {str(e)}"
            self.root.after(0, lambda: self.update_video_status(f"❌ ERROR: {error_msg}"))
            import traceback
            self.root.after(0, lambda: self.update_video_status(f"Traceback: {traceback.format_exc()}"))
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, lambda: self.generate_video_btn.config(state="normal", bg="#4CAF50"))
            self.root.after(0, lambda: self.progress_label.config(text="Ready to generate video"))
            self.root.after(0, lambda: self.progress_bar.config(value=0))
    
    def open_output_folder(self):
        """Open the output folder in file explorer"""
        if self.video_output_path:
            folder_path = os.path.dirname(self.video_output_path)
        else:
            folder_path = os.getcwd()
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', folder_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")
    
    def clear_video_results(self):
        """Clear video generation results"""
        self.video_status_display.config(state="normal")
        self.video_status_display.delete("1.0", tk.END)
        self.video_status_display.insert(tk.END, "Video results cleared. Ready for new generation.\n")
        self.video_status_display.config(state="disabled")
        
        self.video_output_path = None

class AudioProcessor:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def align_audio(self, reference_audio, target_audio):
        """Align target audio to reference using cross-correlation"""
        # Use shorter segments for faster processing
        ref_len = min(len(reference_audio), self.sample_rate * 30)  # 30 seconds max
        target_len = min(len(target_audio), self.sample_rate * 30)
        
        ref_segment = reference_audio[:ref_len]
        target_segment = target_audio[:target_len]
        
        # Cross-correlation
        correlation = signal.correlate(ref_segment, target_segment, mode='full')
        lag = correlation.argmax() - (len(target_segment) - 1)
        
        # Apply alignment
        if lag > 0:
            # Target starts later - pad beginning
            aligned_audio = np.concatenate([np.zeros(lag), target_audio])
        else:
            # Target starts earlier - trim beginning
            aligned_audio = target_audio[-lag:]
            
        # Match length to reference
        if len(aligned_audio) < len(reference_audio):
            # Pad end
            padding = len(reference_audio) - len(aligned_audio)
            aligned_audio = np.concatenate([aligned_audio, np.zeros(padding)])
        else:
            # Trim end
            aligned_audio = aligned_audio[:len(reference_audio)]
            
        return aligned_audio
        
    def mix_audio(self, instrumental, vocal, instrumental_gain=None, vocal_gain=None):
        """Mix instrumental and vocal tracks with smart auto-balancing"""
        # Ensure same length
        min_length = min(len(instrumental), len(vocal))
        instrumental = instrumental[:min_length]
        vocal = vocal[:min_length]
        
        # Smart auto-balancing for mixed sources (AI-separated + karaoke)
        if instrumental_gain is None or vocal_gain is None:
            instrumental_gain, vocal_gain = self._calculate_smart_balance(instrumental, vocal)
        
        # Mix with calculated gains
        mixed = (instrumental * instrumental_gain) + (vocal * vocal_gain)
        
        # Intelligent normalization preserving dynamic range
        mixed = self._smart_normalize(mixed)
        
        return mixed
    
    def _calculate_smart_balance(self, instrumental, vocal):
        """Calculate optimal balance for mixed sources (AI-separated + karaoke)"""
        
        # 1. RMS Analysis - Perceptual loudness matching
        instrumental_rms = np.sqrt(np.mean(instrumental**2) + 1e-10)  # Avoid division by zero
        vocal_rms = np.sqrt(np.mean(vocal**2) + 1e-10)
        
        # 2. Frequency-aware analysis (vocal frequency range: 300Hz - 3kHz)
        vocal_freq_energy = self._get_frequency_energy(vocal, 300, 3000)
        instrumental_freq_energy = self._get_frequency_energy(instrumental, 300, 3000)
        
        # 3. Dynamic range analysis
        vocal_dynamic_range = np.max(np.abs(vocal)) / (vocal_rms + 1e-10)
        instrumental_dynamic_range = np.max(np.abs(instrumental)) / (instrumental_rms + 1e-10)
        
        # 4. Calculate base ratio from RMS (perceptual loudness)
        rms_ratio = vocal_rms / instrumental_rms
        
        # 5. Frequency masking prevention
        # If instrumental is too loud in vocal frequencies, reduce it
        freq_ratio = vocal_freq_energy / (instrumental_freq_energy + 1e-10)
        
        # 6. Smart gain calculation
        # Target: vocal should be 2-4dB above instrumental in vocal frequencies
        target_vocal_prominence = 1.5  # ~3dB advantage
        
        if freq_ratio < target_vocal_prominence:
            # Vocal is being masked, boost vocal or reduce instrumental
            vocal_boost = min(2.0, target_vocal_prominence / freq_ratio)
            vocal_gain = vocal_boost
            instrumental_gain = 0.7  # Reduce instrumental to make space
        else:
            # Good balance, use RMS-based ratio with limits
            vocal_gain = np.clip(1.0, 0.5, 2.0)  # Keep vocal natural
            instrumental_gain = np.clip(0.8 / rms_ratio, 0.3, 1.0)  # Adjust instrumental
        
        # 7. Dynamic range preservation
        # If karaoke vocal has poor dynamic range, apply gentle compression
        if vocal_dynamic_range < 3.0:  # Very compressed vocal
            vocal_gain *= 0.9  # Slight reduction to avoid harshness
        
        return instrumental_gain, vocal_gain
    
    def _get_frequency_energy(self, audio, low_freq, high_freq):
        """Get energy in specific frequency range"""
        # Simple frequency analysis using FFT
        fft = np.fft.rfft(audio)
        freqs = np.fft.rfftfreq(len(audio), 1/self.sample_rate)
        
        # Find frequency bin indices
        low_bin = np.argmax(freqs >= low_freq)
        high_bin = np.argmax(freqs >= high_freq)
        
        # Calculate energy in range
        energy = np.sum(np.abs(fft[low_bin:high_bin])**2)
        return energy + 1e-10  # Avoid zero
    
    def _smart_normalize(self, mixed):
        """Intelligent normalization preserving dynamic range"""
        max_val = np.max(np.abs(mixed))
        
        if max_val > 1.0:
            # Soft limiting instead of hard clipping
            # Preserve dynamic range while preventing clipping
            compression_ratio = 0.95 / max_val
            mixed = mixed * compression_ratio
        elif max_val < 0.3:
            # If too quiet, gently boost
            boost = min(2.0, 0.7 / max_val)
            mixed = mixed * boost
            
        return mixed

class MusicAnalyzer:
    """Music analysis class using librosa"""
    
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        
    def analyze_audio_file(self, file_path):
        """Perform comprehensive music analysis"""
        if not AUDIO_LIBS_AVAILABLE:
            raise ImportError("Audio processing libraries not available")
            
        import time
        start_time = time.time()
        
        # Load audio
        y, sr = librosa.load(file_path, sr=self.sample_rate)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Basic features
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        
        # Key detection (simplified)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key = self._detect_key(chroma)
        
        # Energy analysis
        rms = librosa.feature.rms(y=y)[0]
        energy = float(np.mean(rms))
        
        # Valence estimation (using spectral features)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        valence = min(1.0, float(np.mean(spectral_centroid) / (sr/4)))
        
        # Section analysis
        sections = self._analyze_sections(y, sr, duration, tempo)
        
        # Energy curve for time series
        hop_length = 512
        frame_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=hop_length)
        energy_timestamps = frame_times[::50].tolist()  # Downsample for smaller JSON
        energy_values = rms[::50].tolist()
        
        processing_time = time.time() - start_time
        
        return {
            'duration': duration,
            'tempo': float(tempo),
            'tempo_confidence': 0.85,
            'key': key,
            'key_confidence': 0.8,
            'energy': energy,
            'dynamic_range': float(np.std(rms)),
            'loudness': -14.0,  # Placeholder
            'valence': valence,
            'beat_times': beat_times,
            'sections': sections,
            'energy_timestamps': energy_timestamps,
            'energy_values': energy_values,
            'processing_time': processing_time,
            'overall_confidence': 0.8
        }
        
    def _detect_key(self, chroma):
        """Simple key detection"""
        key_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Major key template (simplified)
        major_template = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        
        chroma_mean = np.mean(chroma, axis=1)
        correlations = []
        
        for i in range(12):
            shifted_template = np.roll(major_template, i)
            correlation = np.corrcoef(chroma_mean, shifted_template)[0, 1]
            correlations.append(correlation)
            
        best_key_idx = np.argmax(correlations)
        return key_names[best_key_idx]
        
    def _analyze_sections(self, y, sr, duration, tempo):
        """Analyze music sections"""
        sections = []
        section_length = 15  # seconds per section
        
        for start in np.arange(0, duration, section_length):
            end = min(start + section_length, duration)
            
            # Extract segment
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            segment = y[start_sample:end_sample]
            
            if len(segment) < sr:  # Skip very short segments
                continue
                
            # Analyze segment
            segment_rms = librosa.feature.rms(y=segment)[0]
            segment_energy = float(np.mean(segment_rms))
            
            # Estimate section type based on position and energy
            section_type = self._classify_section(start, duration, segment_energy)
            
            # Simple valence for segment
            segment_centroid = librosa.feature.spectral_centroid(y=segment, sr=sr)[0]
            segment_valence = min(1.0, float(np.mean(segment_centroid) / (sr/4)))
            
            sections.append({
                'start_time': start,
                'end_time': end,
                'duration': end - start,
                'type': section_type,
                'tempo': float(tempo),  # Use global tempo for now
                'energy': segment_energy,
                'valence': segment_valence,
                'loudness': -14.0,  # Placeholder
                'key_stability': 0.8,
                'harmonic_complexity': segment_energy * 0.7,  # Rough estimate
                'rhythmic_density': segment_energy * 0.8,
                'mood_tags': self._get_mood_tags(segment_energy, segment_valence)
            })
            
        return sections
        
    def _classify_section(self, start_time, total_duration, energy):
        """Simple section classification"""
        position_ratio = start_time / total_duration
        
        if position_ratio < 0.15:
            return "intro"
        elif position_ratio > 0.85:
            return "outro"  
        elif energy > 0.6:
            return "chorus"
        elif energy > 0.4:
            return "verse"
        else:
            return "bridge"
            
    def _get_mood_tags(self, energy, valence):
        """Generate mood tags based on energy and valence"""
        tags = []
        
        if energy > 0.7:
            tags.append("energetic")
        elif energy > 0.4:
            tags.append("moderate")
        else:
            tags.append("calm")
            
        if valence > 0.6:
            tags.append("positive")
        elif valence > 0.4:
            tags.append("neutral")
        else:
            tags.append("melancholic")
            
        return tags

def main():
    if DRAG_DROP_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = AudioProcessorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()