#!/usr/bin/env python3

"""
Fix color to pure single white and make thicker lines
Try different methods to get solid white color
"""

import subprocess
import os

def create_pure_white_thick():
    """Create pure white thick circular visualizer"""
    
    audio_file = "Gnarls Barkley - Crazy (Official Video) [4K Remaster].mp3"
    test_duration = 15
    
    print("Creating PURE WHITE thick circular visualizer...")
    
    try:
        # Create background
        bg_video = "bg_pure.mp4"
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
        
        # Test different white color methods
        white_tests = [
            {
                'name': 'pure_white_rgb',
                'filter': 'showwaves=mode=line:s=1080x1080:colors=0xFFFFFF',
                'description': 'Pure white RGB hex'
            },
            {
                'name': 'thick_p2p_white',
                'filter': 'showwaves=mode=p2p:s=1080x1080:colors=0xFFFFFF',
                'description': 'Thick p2p mode with white'
            },
            {
                'name': 'point_white',
                'filter': 'showwaves=mode=point:s=1080x1080:colors=0xFFFFFF',
                'description': 'Point mode (thicker) with white'
            }
        ]
        
        for test in white_tests:
            print(f"Testing {test['description']}...")
            
            # Step 1: Create waveform
            wave_file = f"wave_{test['name']}.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_file,
                '-t', str(test_duration),
                '-filter_complex',
                f"[0:a]{test['filter']}[v]",
                '-map', '[v]',
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                wave_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  FAILED: {test['name']} waveform - {result.stderr}")
                continue
            
            # Step 2: Make circular
            circular_file = f"circular_{test['name']}.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', wave_file,
                '-filter_complex',
                "geq='p(mod((2*W/(2*PI))*(PI+atan2(0.5*H-Y,X-W/2)),W), H-2*hypot(0.5*H-Y,X-W/2))'",
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                circular_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                print(f"  FAILED: {test['name']} circular - {result.stderr}")
                continue
            
            # Step 3: Overlay
            final_file = f"PURE_WHITE_{test['name'].upper()}.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', bg_video,
                '-i', circular_file,
                '-filter_complex',
                '[1:v]colorkey=Black:0.1:0.1[ck];[0:v][ck]overlay=(W-w)/2:(H-h)/2[outv]',
                '-map', '[outv]',
                '-map', '0:a',
                '-pix_fmt', 'yuv420p',
                final_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  FAILED: {test['name']} final - {result.stderr}")
                continue
            
            print(f"  SUCCESS: {final_file}")
        
        print("\nPURE WHITE tests complete!")
        print("Check these files for pure white color:")
        print("- PURE_WHITE_PURE_WHITE_RGB.mp4 (hex color)")
        print("- PURE_WHITE_THICK_P2P_WHITE.mp4 (thicker p2p mode)")
        print("- PURE_WHITE_POINT_WHITE.mp4 (point mode - thickest)")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    create_pure_white_thick()