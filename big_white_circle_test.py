#!/usr/bin/env python3

"""
Create big white circular visualizer - 1080px size, pure white color
Based on the yellow lines that user liked
"""

import subprocess
import os

def create_big_white_circle():
    """Create big white circular visualizer"""
    
    audio_file = "Gnarls Barkley - Crazy (Official Video) [4K Remaster].mp3"
    test_duration = 15
    
    print("Creating BIG WHITE circular visualizer (1080px)...")
    
    try:
        # Step 1: Create background video
        bg_video = "bg_1080.mp4"
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
        print("Background ready")
        
        # Step 2: Create BIG white waveform (1080x1080 instead of 800x800)
        big_wave = "big_white_wave.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', audio_file,
            '-t', str(test_duration),
            '-filter_complex',
            # Pure white color, 1080x1080 size, line mode like the one you liked
            'showwaves=mode=line:s=1080x1080:colors=white[v]',
            '-map', '[v]',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            big_wave
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Big waveform failed: {result.stderr}")
            return
        print("Big white waveform created")
        
        # Step 3: Make it circular (1080x1080)
        big_circular = "big_white_circular.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', big_wave,
            '-filter_complex',
            "geq='p(mod((2*W/(2*PI))*(PI+atan2(0.5*H-Y,X-W/2)),W), H-2*hypot(0.5*H-Y,X-W/2))'",
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            big_circular
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Big circular failed: {result.stderr}")
            return
        print("Big white circular created")
        
        # Step 4: Overlay on background - 1080px circle on 1920x1080 background
        final_big = "BIG_WHITE_CIRCULAR_FINAL.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-i', bg_video,
            '-i', big_circular,
            '-filter_complex',
            # Center the 1080x1080 circle on 1920x1080 background
            '[1:v]colorkey=Black:0.1:0.1[ck];[0:v][ck]overlay=(W-w)/2:(H-h)/2[outv]',
            '-map', '[outv]',
            '-map', '0:a',
            '-pix_fmt', 'yuv420p',
            final_big
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"Final big overlay failed: {result.stderr}")
            return
        
        print(f"SUCCESS: {final_big}")
        print("\nBIG WHITE CIRCULAR VISUALIZER COMPLETE!")
        print("Check BIG_WHITE_CIRCULAR_FINAL.mp4")
        print("- 1080px diameter (full video height)")
        print("- Pure white color")
        print("- Centered on 1920x1080 background")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    create_big_white_circle()