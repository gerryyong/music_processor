#!/usr/bin/env python3

"""
Smart solution: Create visualizer with background.png as the background
Instead of black background + overlay, use background.png directly in showwaves
"""

import subprocess
import os

def create_visualizer_with_background():
    """Create visualizer with background.png as the background from the start"""
    
    audio_file = "Gnarls Barkley - Crazy (Official Video) [4K Remaster].mp3"
    test_duration = 15
    
    print("Creating visualizer WITH background.png as background...")
    
    try:
        # Method 1: Create waveform with background image as base
        print("Method 1: Waveform directly on background image...")
        output1 = "direct_bg_waveform.mp4"
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', 'background.png',
            '-i', audio_file,
            '-t', str(test_duration),
            '-filter_complex',
            # Scale background to match our visualizer size, then add waveform on top
            '[0:v]scale=1200:1200[bg];'
            '[1:a]aformat=channel_layouts=mono,showwaves=mode=p2p:s=1200x1200:colors=Blue[waves];'
            '[bg][waves]blend=all_mode=screen[v]',
            '-map', '[v]',
            '-pix_fmt', 'yuv420p',
            '-r', '30',
            output1
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Method 1 failed: {result.stderr}")
        else:
            print(f"SUCCESS: {output1}")
        
        # Method 2: Create circular version with background
        print("Method 2: Creating circular version with background...")
        if os.path.exists(output1):
            output2 = "circular_with_bg.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', output1,
                '-filter_complex',
                "geq='p(mod((2*W/(2*PI))*(PI+atan2(0.5*H-Y,X-W/2)),W), H-2*hypot(0.5*H-Y,X-W/2))'",
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                output2
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                print(f"Method 2 failed: {result.stderr}")
            else:
                print(f"SUCCESS: {output2}")
        
        # Method 3: Final video - scale circular to fit on 1920x1080 background
        print("Method 3: Final video with proper background scaling...")
        if os.path.exists(output2):
            final_bg = "final_background_video.mp4"
            
            # First create 1920x1080 background video
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', 'background.png',
                '-i', audio_file,
                '-t', str(test_duration),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                '-s', '1920x1080',
                final_bg
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"Background creation failed: {result.stderr}")
            else:
                # Now overlay the circular visualizer on center
                final_output = "FINAL_WITH_BACKGROUND.mp4"
                cmd = [
                    'ffmpeg', '-y',
                    '-i', final_bg,
                    '-i', output2,
                    '-filter_complex',
                    '[1:v]scale=800:800[scaled];[0:v][scaled]overlay=(W-w)/2:(H-h)/2[outv]',
                    '-map', '[outv]',
                    '-map', '0:a',
                    '-pix_fmt', 'yuv420p',
                    final_output
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    print(f"Final overlay failed: {result.stderr}")
                else:
                    print(f"SUCCESS: {final_output}")
        
        print("\nTEST COMPLETE!")
        print("Check FINAL_WITH_BACKGROUND.mp4 - should show blue circular visualizer with your background!")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    create_visualizer_with_background()