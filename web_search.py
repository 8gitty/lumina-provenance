import os
import requests
from google.cloud import vision

def pin_image_to_ipfs(image_path: str) -> str:
    """Uploads an image file to catbox.moe for instant, direct, public URL access."""
    url = "https://catbox.moe/user/api.php"
    with open(image_path, "rb") as f:
        response = requests.post(url, data={"reqtype": "fileupload"}, files={"fileToUpload": f})
        
    if response.status_code == 200:
        return response.text
    return None

def search_web_for_image(image_path: str):
    """
    Searches the web for matching images/entities.
    Tries Google Cloud Vision API Web Detection first.
    Falls back to SerpApi by temporarily uploading the image to get a public URL.
    """
    results = []
    
    # Try Google Vision API first
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            client = vision.ImageAnnotatorClient()
            with open(image_path, "rb") as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            
            response = client.web_detection(image=image)
            
            # Check if there is an error (e.g. billing not enabled)
            if response.error.message:
                print(f"Vision API Error: {response.error.message}")
            else:
                annotations = response.web_detection
                if annotations.pages_with_matching_images:
                    for page in annotations.pages_with_matching_images:
                        score = 0.0
                        if page.full_matching_images: score = 0.95
                        elif page.partial_matching_images: score = 0.75
                        else: score = 0.50
                            
                        results.append({
                            "url": page.url,
                            "page_title": page.page_title,
                            "score": score,
                            "source": "Google Vision API",
                            "thumbnail": None
                        })
        except Exception as e:
            print(f"Google Vision API failed: {e}")
            
    # Fallback to SerpApi Google Lens if Vision failed or returned no results
    if not results and os.environ.get("SERPAPI_API_KEY"):
        print("Vision API returned no results or failed. Falling back to SerpApi Google Lens...")
        try:
            # 1. We need a public URL for SerpApi to search an image.
            # Upload to catbox.moe for a temporary public URL.
            public_image_url = pin_image_to_ipfs(image_path)
            if public_image_url:
                print(f"Uploaded image for SerpApi search: {public_image_url}")
                
                # 2. Call SerpApi Google Lens
                from serpapi import GoogleSearch
                params = {
                    "engine": "google_lens",
                    "url": public_image_url,
                    "api_key": os.environ.get("SERPAPI_API_KEY")
                }
                search = GoogleSearch(params)
                serp_results = search.get_dict()
                
                if "visual_matches" in serp_results:
                    for match in serp_results["visual_matches"][:10]: # take top 10
                        # Try to find a link
                        link = match.get("link")
                        if link:
                            results.append({
                                "url": link,
                                "page_title": match.get("title", "Visual Match"),
                                "score": 0.85, # SerpApi doesn't give a score, assume high confidence
                                "source": "SerpApi Google Lens",
                                "thumbnail": match.get("thumbnail")
                            })
        except Exception as e:
            print(f"SerpApi fallback failed: {e}")
            
    # Sort results by score descending
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results
