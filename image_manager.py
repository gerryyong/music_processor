import requests
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from PIL import Image
import urllib.parse
import time

@dataclass
class ImageResult:
    """Represents a single image search result"""
    id: str
    url: str
    download_url: str
    description: str
    photographer: str
    width: int
    height: int
    color: str

class UnsplashImageManager:
    """Manages image search and download from Unsplash API"""
    
    def __init__(self, access_key: str = None):
        """
        Initialize with Unsplash API access key
        Get your free API key at: https://unsplash.com/developers
        """
        self.access_key = access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.base_url = "https://api.unsplash.com"
        self.headers = {
            'Authorization': f'Client-ID {self.access_key}',
            'Accept-Version': 'v1'
        }
        
        if not self.access_key:
            raise ValueError(
                "Unsplash API key required. Set UNSPLASH_ACCESS_KEY environment variable "
                "or pass access_key parameter. Get free key at: https://unsplash.com/developers"
            )
    
    def search_images_by_mood(self, mood_data: Dict[str, Any], count: int = 10) -> List[ImageResult]:
        """
        Search for images based on music mood analysis
        
        Args:
            mood_data: Section data from music analysis JSON
            count: Number of images to fetch (max 30)
        """
        # Build search query from mood data
        query = self._build_search_query(mood_data)
        
        # Search parameters
        params = {
            'query': query,
            'per_page': min(count, 30),
            'order_by': 'relevant',
            'content_filter': 'high',  # Family-friendly content
            'orientation': 'landscape'  # Good for video backgrounds
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/search/photos",
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            images = []
            
            for photo in data.get('results', []):
                image = ImageResult(
                    id=photo['id'],
                    url=photo['urls']['regular'],
                    download_url=photo['urls']['full'],
                    description=photo.get('alt_description', '') or photo.get('description', ''),
                    photographer=photo['user']['name'],
                    width=photo['width'],
                    height=photo['height'],
                    color=photo.get('color', '#000000')
                )
                images.append(image)
            
            return images
            
        except requests.exceptions.RequestException as e:
            print(f"Error searching images: {e}")
            return []
    
    def _build_search_query(self, mood_data: Dict[str, Any]) -> str:
        """Build Unsplash search query from mood analysis"""
        query_parts = []
        
        # Add mood-based keywords
        mood = mood_data.get('mood', 'neutral')
        colors = mood_data.get('colors', [])
        section_type = mood_data.get('type', 'verse')
        energy = mood_data.get('energy', 0.5)
        
        # Base visual themes by section type
        section_themes = {
            'intro': ['landscape', 'abstract', 'morning', 'horizon'],
            'verse': ['nature', 'story', 'people', 'lifestyle'],
            'chorus': ['dynamic', 'celebration', 'action', 'vibrant'],
            'bridge': ['transition', 'artistic', 'abstract', 'emotional'],
            'outro': ['sunset', 'peaceful', 'ending', 'calm']
        }
        
        # Add section-specific themes
        themes = section_themes.get(section_type, ['nature'])
        query_parts.extend(themes[:2])  # Take first 2 themes
        
        # Add color/mood keywords
        if colors:
            # Convert color descriptors to search terms
            color_map = {
                'warm': 'golden warm',
                'bright': 'bright colorful',
                'energetic': 'vibrant dynamic',
                'soft': 'soft pastel',
                'light': 'light airy',
                'peaceful': 'serene peaceful',
                'dark': 'dark moody',
                'moody': 'atmospheric dramatic',
                'atmospheric': 'foggy misty',
                'intense': 'dramatic powerful',
                'dramatic': 'cinematic epic',
                'bold': 'striking bold',
                'neutral': 'minimalist clean',
                'balanced': 'harmonious',
                'natural': 'organic natural'
            }
            
            for color in colors[:2]:  # Take first 2 colors
                if color in color_map:
                    query_parts.append(color_map[color])
        
        # Add energy-based modifiers
        if energy > 0.7:
            query_parts.append('dynamic action')
        elif energy < 0.3:
            query_parts.append('calm serene')
        
        # Combine and clean up query
        query = ' '.join(query_parts)
        
        # Remove duplicates and limit length
        words = []
        for word in query.split():
            if word not in words:
                words.append(word)
        
        return ' '.join(words[:8])  # Limit to 8 keywords
    
    def download_image(self, image: ImageResult, output_dir: str = "images", 
                      filename: str = None) -> Optional[str]:
        """
        Download an image to local storage
        
        Args:
            image: ImageResult to download
            output_dir: Directory to save image
            filename: Custom filename (optional)
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            if not filename:
                ext = '.jpg'  # Unsplash images are typically JPEG
                safe_desc = "".join(c for c in (image.description or image.id) if c.isalnum() or c in (' ', '_')).strip()[:50]
                filename = f"{image.id}_{safe_desc}{ext}".replace(' ', '_')
            
            file_path = os.path.join(output_dir, filename)
            
            # Download image
            response = requests.get(image.download_url, timeout=30)
            response.raise_for_status()
            
            # Save to file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Trigger download tracking (Unsplash API requirement)
            self._track_download(image.id)
            
            return file_path
            
        except Exception as e:
            print(f"Error downloading image {image.id}: {e}")
            return None
    
    def _track_download(self, photo_id: str):
        """Track download for Unsplash API compliance"""
        try:
            requests.get(
                f"{self.base_url}/photos/{photo_id}/download",
                headers=self.headers,
                timeout=5
            )
        except:
            pass  # Download tracking is optional but recommended
    
    def process_music_analysis(self, analysis_json: Dict[str, Any], 
                             images_per_section: int = 3) -> Dict[str, List[ImageResult]]:
        """
        Process complete music analysis and fetch images for each section
        
        Args:
            analysis_json: Music analysis JSON from audio processor
            images_per_section: Number of images to fetch per section
            
        Returns:
            Dictionary mapping section indices to image lists
        """
        sections_images = {}
        
        video_sections = analysis_json.get('video_sections', [])
        
        for i, section in enumerate(video_sections):
            print(f"Fetching images for section {i+1}/{len(video_sections)}: {section.get('type', 'unknown')} "
                  f"({section.get('start', 0):.1f}s - {section.get('end', 0):.1f}s)")
            
            # Search for images matching this section's mood
            images = self.search_images_by_mood(section, count=images_per_section)
            sections_images[f"section_{i}"] = images
            
            # Rate limiting - be nice to Unsplash API
            time.sleep(0.5)
        
        return sections_images
    
    def download_section_images(self, sections_images: Dict[str, List[ImageResult]], 
                              output_dir: str = "section_images") -> Dict[str, List[str]]:
        """
        Download all images for all sections
        
        Returns:
            Dictionary mapping section keys to lists of local file paths
        """
        downloaded_paths = {}
        
        for section_key, images in sections_images.items():
            section_dir = os.path.join(output_dir, section_key)
            section_paths = []
            
            for i, image in enumerate(images):
                filename = f"{section_key}_image_{i+1}_{image.id}.jpg"
                file_path = self.download_image(image, section_dir, filename)
                
                if file_path:
                    section_paths.append(file_path)
                    print(f"Downloaded: {filename}")
                else:
                    print(f"Failed to download image {image.id}")
                
                # Rate limiting
                time.sleep(0.3)
            
            downloaded_paths[section_key] = section_paths
        
        return downloaded_paths

class ImageProcessor:
    """Process images for video compatibility"""
    
    @staticmethod
    def resize_for_video(image_path: str, target_width: int = 1920, 
                        target_height: int = 1080, output_path: str = None) -> Optional[str]:
        """
        Resize and crop image to video dimensions (16:9 aspect ratio)
        
        Args:
            image_path: Path to source image
            target_width: Target width in pixels
            target_height: Target height in pixels  
            output_path: Output path (optional)
            
        Returns:
            Path to processed image or None if failed
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Calculate scaling to cover the target dimensions
                img_ratio = img.width / img.height
                target_ratio = target_width / target_height
                
                if img_ratio > target_ratio:
                    # Image is wider - scale by height
                    scale = target_height / img.height
                    new_width = int(img.width * scale)
                    new_height = target_height
                else:
                    # Image is taller - scale by width  
                    scale = target_width / img.width
                    new_width = target_width
                    new_height = int(img.height * scale)
                
                # Resize image
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center crop to exact dimensions
                left = (new_width - target_width) // 2
                top = (new_height - target_height) // 2
                right = left + target_width
                bottom = top + target_height
                
                img = img.crop((left, top, right, bottom))
                
                # Generate output path
                if not output_path:
                    base, ext = os.path.splitext(image_path)
                    output_path = f"{base}_video{ext}"
                
                # Save processed image
                img.save(output_path, 'JPEG', quality=90)
                
                return output_path
                
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return None
    
    @staticmethod
    def process_section_images(section_paths: List[str], output_dir: str = None) -> List[str]:
        """Process all images in a section for video compatibility"""
        processed_paths = []
        
        for image_path in section_paths:
            if output_dir:
                filename = os.path.basename(image_path)
                base, ext = os.path.splitext(filename)
                output_path = os.path.join(output_dir, f"{base}_processed{ext}")
            else:
                output_path = None
            
            processed_path = ImageProcessor.resize_for_video(image_path, output_path=output_path)
            
            if processed_path:
                processed_paths.append(processed_path)
        
        return processed_paths

def main():
    """Test the image manager"""
    # Example usage
    sample_analysis = {
        "song": "test_song.mp3",
        "duration": 180.0,
        "overall_mood": {
            "energy": 0.75,
            "vibe": "energetic_happy",
            "tempo": 128,
            "key": "G"
        },
        "video_sections": [
            {
                "start": 0.0,
                "end": 30.0,
                "type": "intro",
                "energy": 0.3,
                "mood": "calm",
                "colors": ["soft", "light", "peaceful"]
            },
            {
                "start": 30.0,
                "end": 90.0,
                "type": "chorus",
                "energy": 0.9,
                "mood": "high",
                "colors": ["warm", "bright", "energetic"]
            }
        ]
    }
    
    print("Image Manager Test")
    print("==================")
    print("To test with real API:")
    print("1. Get free Unsplash API key: https://unsplash.com/developers")
    print("2. Set environment variable: UNSPLASH_ACCESS_KEY=your_key_here")
    print("3. Run this script")
    
    # Check if API key is available
    api_key = os.getenv('UNSPLASH_ACCESS_KEY')
    if not api_key:
        print("\nNo API key found. Please set UNSPLASH_ACCESS_KEY environment variable.")
        return
    
    try:
        # Initialize image manager
        manager = UnsplashImageManager(api_key)
        
        # Process music analysis
        print(f"\nProcessing music analysis for: {sample_analysis['song']}")
        sections_images = manager.process_music_analysis(sample_analysis, images_per_section=2)
        
        # Download images
        print("\nDownloading images...")
        downloaded_paths = manager.download_section_images(sections_images)
        
        # Process images for video
        print("\nProcessing images for video compatibility...")
        for section_key, paths in downloaded_paths.items():
            processed_paths = ImageProcessor.process_section_images(paths)
            print(f"Processed {len(processed_paths)} images for {section_key}")
        
        print("\nImage management test completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    main()