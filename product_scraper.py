import requests
from bs4 import BeautifulSoup
import json
import re

def extract_product_info(url):
    """
    Extract product information from a URL.
    
    Args:
        url (str): The URL of the product page
        
    Returns:
        dict: A dictionary containing product information (name, purchase_url)
        or None if extraction fails
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Attempting to extract product info from: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # NARS website
        if 'narscosmetics.com' in url:
            # Extract product name
            product_name = soup.select_one('h1.product-name')
            if product_name:
                product_name = product_name.text.strip()
                print(f"Found product name: {product_name}")
            else:
                print("Could not find product name")
                product_name = None
            
            # Extract product ID from URL (for debugging only)
            product_id = None
            if url:
                # Try to extract the product ID from the URL (usually the last part)
                match = re.search(r'/(\d+)\.html', url)
                if match:
                    product_id = match.group(1)
                    print(f"Extracted product ID from URL: {product_id}")
            
            # Image URL extraction is commented out as it's flaky
            # We'll just set it to None
            image_url = None
            
            """
            # Commented out image URL extraction logic
            if product_id:
                # Try different patterns for NARS image URLs
                possible_image_urls = [
                    # Orgasm Collection specific URL pattern
                    f"https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dwe96baba9/2023/January/Makeup/OrgasmCollection/{product_id}_OrgasmCollection_EyeshadowPalette_1.jpg?sw=856&sh=750&sm=fit",
                    
                    # Light Reflecting Powder pattern
                    f"https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw9b8d47cc/2024/June/LRPowder/{product_id}_1.jpg?sw=856&sh=750&sm=fit",
                    
                    # Orgasm Rising pattern
                    f"https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw9b8d47cc/2024/June/OrgasmRising/{product_id}_1.jpg?sw=856&sh=750&sm=fit",
                    
                    # Generic hi-res patterns
                    f"https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw5f5e8e2f/hi-res/{product_id}.jpg",
                    f"https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw5f5e8e2f/hi-res/{product_id}_1.jpg",
                    f"https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dw9b8d47cc/hi-res/{product_id}_1.jpg?sw=856&sh=750&sm=fit"
                ]
                
                print(f"Trying possible image URLs for product ID: {product_id}")
                # Try each URL to see if it exists
                for img_url in possible_image_urls:
                    try:
                        print(f"Checking image URL: {img_url}")
                        img_response = requests.head(img_url, headers=headers, timeout=5)
                        if img_response.status_code == 200:
                            image_url = img_url
                            print(f"Found valid image URL: {image_url}")
                            break
                    except Exception as e:
                        print(f"Error checking image URL {img_url}: {str(e)}")
                        continue
            
            # If we couldn't construct a valid URL, try to extract it from the page
            if not image_url:
                print("Could not construct valid image URL, trying to extract from page")
                
                # Look for data-lgimg attribute which often contains high-res image
                high_res_img = soup.select_one('[data-lgimg]')
                if high_res_img and 'data-lgimg' in high_res_img.attrs:
                    image_url = high_res_img['data-lgimg']
                    if not image_url.startswith('http'):
                        image_url = f"https://www.narscosmetics.com{image_url}"
                    print(f"Found image URL in data-lgimg attribute: {image_url}")
                
                # Try to find the high-resolution image URL in the page source
                if not image_url:
                    # Look for JSON data in the page that contains image URLs
                    script_tags = soup.find_all('script')
                    
                    for script in script_tags:
                        if script.string and 'pdpImages' in script.string:
                            try:
                                print("Found script with pdpImages")
                                # Find JSON-like data in the script
                                json_match = re.search(r'pdpImages\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                                if json_match:
                                    images_data = json.loads(json_match.group(1))
                                    if images_data and len(images_data) > 0:
                                        # Get the first high-res image
                                        for img in images_data:
                                            if isinstance(img, dict) and 'url' in img:
                                                image_url = img['url']
                                                if not image_url.startswith('http'):
                                                    image_url = f"https://www.narscosmetics.com{image_url}"
                                                print(f"Extracted image URL from JSON: {image_url}")
                                                break
                            except Exception as e:
                                print(f"Error extracting image URL from JSON: {str(e)}")
                    
                    # Fallback to primary-image if JSON extraction failed
                    if not image_url:
                        print("Trying to find primary-image element")
                        image_element = soup.select_one('img.primary-image')
                        if image_element:
                            if 'src' in image_element.attrs:
                                image_url = image_element['src']
                                print(f"Found image URL in src attribute: {image_url}")
                            elif 'data-src' in image_element.attrs:
                                image_url = image_element['data-src']
                                print(f"Found image URL in data-src attribute: {image_url}")
                        
                        # If image URL is relative, make it absolute
                        if image_url and not image_url.startswith('http'):
                            if image_url.startswith('//'):
                                image_url = 'https:' + image_url
                            else:
                                image_url = f"https://www.narscosmetics.com{image_url}"
                            print(f"Converted to absolute URL: {image_url}")
                
                # Try one more approach - look for data-zoom-image attribute
                if not image_url or "base64" in image_url:
                    print("Trying to find elements with data-zoom-image attribute")
                    zoom_image_elements = soup.select('[data-zoom-image]')
                    if zoom_image_elements:
                        for element in zoom_image_elements:
                            if 'data-zoom-image' in element.attrs:
                                image_url = element['data-zoom-image']
                                if not image_url.startswith('http'):
                                    if image_url.startswith('//'):
                                        image_url = 'https:' + image_url
                                    else:
                                        image_url = f"https://www.narscosmetics.com{image_url}"
                                print(f"Found image URL in data-zoom-image attribute: {image_url}")
                                break
            
            # Fallback for Orgasm Collection Eyeshadow Palette
            if product_id == "0194251135892" and (not image_url or "base64" in image_url):
                image_url = "https://www.narscosmetics.com/dw/image/v2/BBSK_PRD/on/demandware.static/-/Sites-itemmaster_NARS/default/dwe96baba9/2023/January/Makeup/OrgasmCollection/0194251135892_OrgasmCollection_EyeshadowPalette_1.jpg?sw=856&sh=750&sm=fit"
                print(f"Using hardcoded URL for Orgasm Collection Eyeshadow Palette: {image_url}")
            """
            
            # Print debug info
            print(f"Final Product Name: {product_name}")
            print(f"Final Product ID: {product_id}")
            # print(f"Final Image URL: {image_url}")
            
            return {
                'name': product_name,
                # 'image_url': image_url,  # Commented out as it's flaky
                'purchase_url': url
            }
        
        # Add more website handlers as needed
        
        # If no handler matched
        return None
        
    except Exception as e:
        print(f"Error extracting product info: {str(e)}")
        return None

# Test the function directly
if __name__ == "__main__":
    test_url = "https://www.narscosmetics.com/USA/orgasm-rising-eyeshadow-palette/0194251135892.html"
    result = extract_product_info(test_url)
    
    print("\nFinal Result:")
    print(json.dumps(result, indent=2)) 