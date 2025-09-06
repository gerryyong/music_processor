#!/usr/bin/env python3

"""
Direct circular visualizer - create circular pattern directly from audio
No linear->circular conversion, no pink overlay
"""

import subprocess
import os

def create_direct_circular():
    """Create circular visualizer directly from audio"""
    
    audio_file = "Gnarls Barkley - Crazy (Official Video) [4K Remaster].mp3"
    test_duration = 15
    
    print("Creating DIRECT circular visualizer from audio...")
    
    try:
        # Method 1: Try different approach - create background + simple overlay
        print("Method 1: Background + simple waveform overlay...")
        
        # Step 1: Create background video
        bg_video = "clean_background.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', 'background.png',
            '-i', audio_file,
            '-t', str(test_duration),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            '-s', '1920x1080',
            bg_video
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Background failed: {result.stderr}")
            return
        print("Background created")
        
        # Step 2: Create simple waveform (no background)
        wave_video = "simple_wave.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', audio_file,
            '-t', str(test_duration),
            '-filter_complex',
            'aformat=channel_layouts=mono,showwaves=mode=p2p:s=800x800:colors=Blue[v]',
            '-map', '[v]',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            wave_video
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Waveform failed: {result.stderr}")
            return
        print("Simple waveform created")
        
        # Step 3: Make waveform circular
        circular_wave = "circular_simple.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', wave_video,
            '-filter_complex',
            "geq='p(mod((2*W/(2*PI))*(PI+atan2(0.5*H-Y,X-W/2)),W), H-2*hypot(0.5*H-Y,X-W/2))'",
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            circular_wave
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Circular failed: {result.stderr}")
            return
        print("Circular waveform created")
        
        # Step 4: Overlay on background using colorkey to remove black
        final_output = "DIRECT_CIRCULAR_FINAL.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', bg_video,
            '-i', circular_wave,
            '-filter_complex',
            '[1:v]colorkey=Black:0.1:0.1[ck];[0:v][ck]overlay=(W-w)/2:(H-h)/2[outv]',
            '-map', '[outv]',
            '-map', '0:a',
            '-pix_fmt', 'yuv420p',
            final_output
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Final overlay failed: {result.stderr}")
            return
        print(f"SUCCESS: {final_output}")
        
        # Method 2: Try without colorkey (direct overlay)
        final_output2 = "DIRECT_NO_COLORKEY.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', bg_video,
            '-i', circular_wave,
            '-filter_complex',
            '[0:v][1:v]overlay=(W-w)/2:(H-h)/2[outv]',
            '-map', '[outv]',
            '-map', '0:a',
            '-pix_fmt', 'yuv420p',
            final_output2
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"No colorkey overlay failed: {result.stderr}")
        else:
            print(f"SUCCESS: {final_output2}")
        
        print("\nTEST COMPLETE!")
        print("Check these files:")
        print("- DIRECT_CIRCULAR_FINAL.mp4 (with colorkey to remove black)")
        print("- DIRECT_NO_COLORKEY.mp4 (direct overlay)")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    create_direct_circular()