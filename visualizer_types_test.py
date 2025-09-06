#!/usr/bin/env python3

"""
Test different visualizer types:
1. Volume/spectrum bars (showfreqs)
2. Thicker waveforms with bright colors
3. Different showwaves modes with high contrast colors
"""

import subprocess
import os

def test_visualizer_types():
    """Test different visualizer approaches"""
    
    audio_file = "Gnarls Barkley - Crazy (Official Video) [4K Remaster].mp3"
    test_duration = 15
    
    print("Testing different visualizer types...")
    
    # Create background video first (reuse for all tests)
    bg_video = "bg_for_tests.mp4"
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
    
    visualizer_tests = [
        {
            'name': 'spectrum_bars',
            'filter': 'showfreqs=s=800x800:mode=bar:colors=cyan',
            'description': 'Spectrum bars (volume by frequency)'
        },
        {
            'name': 'spectrum_line',
            'filter': 'showfreqs=s=800x800:mode=line:colors=yellow',
            'description': 'Spectrum line (bright yellow)'
        },
        {
            'name': 'thick_white_waves',
            'filter': 'showwaves=mode=p2p:s=800x800:colors=white',
            'description': 'Thick white waveform'
        },
        {
            'name': 'bright_cyan_waves',
            'filter': 'showwaves=mode=point:s=800x800:colors=cyan',
            'description': 'Bright cyan points'
        },
        {
            'name': 'yellow_lines',
            'filter': 'showwaves=mode=line:s=800x800:colors=yellow',
            'description': 'Yellow lines'
        }
    ]
    
    for test in visualizer_tests:
        print(f"Creating {test['description']}...")
        
        try:
            # Step 1: Create visualizer
            viz_file = f"viz_{test['name']}.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_file,
                '-t', str(test_duration),
                '-filter_complex',
                f"[0:a]{test['filter']}[v]",
                '-map', '[v]',
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                viz_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  FAILED: Visualizer creation - {result.stderr}")
                continue
            
            # Step 2: Make circular
            circular_file = f"circular_{test['name']}.mp4"
            cmd = [
                'ffmpeg', '-y',
                '-i', viz_file,
                '-filter_complex',
                "geq='p(mod((2*W/(2*PI))*(PI+atan2(0.5*H-Y,X-W/2)),W), H-2*hypot(0.5*H-Y,X-W/2))'",
                '-pix_fmt', 'yuv420p',
                '-r', '30',
                circular_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"  FAILED: Circular conversion - {result.stderr}")
                continue
            
            # Step 3: Overlay on background
            final_file = f"FINAL_{test['name']}.mp4"
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
                print(f"  FAILED: Final overlay - {result.stderr}")
                continue
            
            print(f"  SUCCESS: {final_file}")
            
        except Exception as e:
            print(f"  FAILED: {test['name']} - {e}")
    
    print("\nVisualizer type tests complete!")
    print("Check FINAL_*.mp4 files to see which type is most visible:")
    print("- FINAL_spectrum_bars.mp4 (volume bars)")
    print("- FINAL_spectrum_line.mp4 (bright yellow spectrum)")
    print("- FINAL_thick_white_waves.mp4 (white waveform)")
    print("- FINAL_bright_cyan_waves.mp4 (cyan points)")
    print("- FINAL_yellow_lines.mp4 (yellow lines)")

if __name__ == "__main__":
    test_visualizer_types()