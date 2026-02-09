#!/usr/bin/env python3
"""
Property Data Extractor
Extracts property information from local HTML files (Idealista format)
"""

from bs4 import BeautifulSoup
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class PropertyData:
    """Data class to hold extracted property information."""
    title: Optional[str] = None
    price: Optional[str] = None
    operation_type: Optional[str] = None  # 'rent' or 'sale'
    property_type: Optional[str] = None  # 'apartment' or 'house'
    location: Optional[Dict[str, str]] = None
    features: List[str] = None
    description: Optional[str] = None
    images: List[str] = None
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.features is None:
            self.features = []
        if self.images is None:
            self.images = []
        if self.location is None:
            self.location = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class PropertyExtractor:
    """Extracts property data from HTML files."""
    
    def __init__(self, html_path: str):
        """
        Initialize the extractor.
        
        Args:
            html_path: Path to the HTML file
        """
        self.html_path = Path(html_path)
        self.soup: Optional[BeautifulSoup] = None
        self._load_html()
    
    def _load_html(self) -> None:
        """Load and parse the HTML file."""
        if not self.html_path.exists():
            raise FileNotFoundError(f"File not found: {self.html_path}")
        
        with open(self.html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        self.soup = BeautifulSoup(html_content, 'html.parser')
    
    def extract(self) -> PropertyData:
        """
        Extract all property data.
        
        Returns:
            PropertyData object with extracted information
        """
        if not self.soup:
            raise ValueError("HTML not loaded")
        
        return PropertyData(
            title=self._extract_title(),
            price=self._extract_price(),
            operation_type=self._extract_operation_type(),
            property_type=self._extract_property_type(),
            location=self._extract_location(),
            features=self._extract_features(),
            description=self._extract_description(),
            images=self._extract_images(),
        )
    
    def _extract_title(self) -> Optional[str]:
        """Extract property title from .main-info__title."""
        title_container = self.soup.select_one('.main-info__title')
        if not title_container:
            return None
        
        # Get main title
        main_title = title_container.select_one('.main-info__title-main')
        minor_title = title_container.select_one('.main-info__title-minor')
        
        parts = []
        if main_title:
            parts.append(main_title.get_text(strip=True))
        if minor_title:
            parts.append(minor_title.get_text(strip=True))
        
        return ', '.join(parts) if parts else None
    
    def _extract_price(self) -> Optional[str]:
        """Extract property price from .info-data."""
        price_element = self.soup.select_one('.info-data .info-data-price')
        if price_element:
            return price_element.get_text(strip=True)
        
        # Fallback to .info-data if specific price element not found
        price_container = self.soup.select_one('.info-data')
        if price_container:
            return price_container.get_text(strip=True)
        
        return None
    
    def _extract_operation_type(self) -> Optional[str]:
        """
        Determine if property is for rent or sale.
        
        Returns:
            'rent', 'sale', or None if cannot determine
        """
        # Check title first
        title = self._extract_title()
        if title:
            title_lower = title.lower()
            if 'alquiler' in title_lower:
                return 'rent'
            elif 'venta' in title_lower or 'compra' in title_lower:
                return 'sale'
        
        # Check page title as fallback
        page_title = self.soup.find('title')
        if page_title:
            title_text = page_title.get_text().lower()
            if 'alquiler' in title_text:
                return 'rent'
            elif 'venta' in title_text or 'compra' in title_text:
                return 'sale'
        
        return None
    
    def _extract_property_type(self) -> Optional[str]:
        """
        Determine if property is a house or apartment.
        
        Returns:
            'apartment', 'house', or None if cannot determine
        """
        # Check typology tag first (most reliable)
        typology = self.soup.select_one('.typology')
        if typology:
            type_text = typology.get_text(strip=True).lower()
            
            # Apartment types
            if any(word in type_text for word in ['piso', 'apartamento', 'ático', 'dúplex', 'estudio']):
                return 'apartment'
            
            # House types
            if any(word in type_text for word in ['casa', 'chalet', 'villa', 'adosado', 'unifamiliar']):
                return 'house'
        
        # Fallback: check title
        title = self._extract_title()
        if title:
            title_lower = title.lower()
            
            # Apartment types
            if any(word in title_lower for word in ['piso', 'apartamento', 'ático', 'dúplex', 'estudio']):
                return 'apartment'
            
            # House types
            if any(word in title_lower for word in ['casa', 'chalet', 'villa', 'adosado', 'unifamiliar']):
                return 'house'
        
        return None
    
    def _extract_location(self) -> Dict[str, str]:
        """
        Extract location information from #headerMap.
        
        Returns:
            Dictionary with location details (street, neighborhood, district, city, etc.)
        """
        location = {}
        
        header_map = self.soup.select_one('#headerMap')
        if not header_map:
            return location
        
        # Get all list items
        list_items = header_map.select('li.header-map-list')
        
        # Map positions to keys (based on typical Idealista structure)
        keys = ['street', 'neighborhood', 'district', 'city', 'province']
        
        for i, item in enumerate(list_items):
            text = item.get_text(strip=True)
            if text and i < len(keys):
                location[keys[i]] = text
        
        return location
    
    def _extract_features(self) -> List[str]:
        """Extract features as a list from .info-features."""
        features_element = self.soup.select_one('.info-features')
        if not features_element:
            return []
        
        # Get all span elements within features
        feature_spans = features_element.find_all('span')
        
        if feature_spans:
            features = []
            for span in feature_spans:
                text = span.get_text(strip=True)
                if text:
                    features.append(text)
            return features
        
        # Fallback: return the whole text
        text = features_element.get_text(strip=True)
        return [text] if text else []
    
    def _extract_description(self) -> Optional[str]:
        """Extract property description from .comment."""
        comment_element = self.soup.select_one('.comment')
        if not comment_element:
            return None
        
        # Get text from all paragraphs within the comment
        paragraphs = comment_element.find_all('p')
        if paragraphs:
            text_parts = [p.get_text(separator=' ', strip=True) for p in paragraphs]
            return '\n\n'.join(text_parts)
        
        # Fallback to entire comment text
        return comment_element.get_text(separator=' ', strip=True)
    
    def _extract_images(self) -> List[str]:
        """
        Extract image URLs from the page.
        
        Only returns WebP images with the URL pattern:
        https://img4.idealista.com/blur/WEB_DETAIL/0/id.pro.es.image.master/
        
        Tries multiple strategies:
        1. JavaScript data in page (adMultimediasInfo)
        2. Images within #main-multimedia
        3. Images within main-image sections
        4. srcset attributes in source tags
        """
        urls = set()  # Use set to avoid duplicates
        
        # Strategy 1: Extract from JavaScript data (most reliable for idealista)
        import re
        page_content = str(self.soup)
        
        # Find all imageDataServiceWebp URLs in the JavaScript
        webp_pattern = r'imageDataServiceWebp["\s:]+([^"]+\.webp)'
        matches = re.findall(webp_pattern, page_content)
        
        for url in matches:
            if self._is_valid_image_url(url):
                urls.add(url)
        
        # Strategy 2: Try #main-multimedia img selector
        multimedia_section = self.soup.select_one('#main-multimedia')
        if multimedia_section:
            images = multimedia_section.find_all('img')
            for img in images:
                url = self._get_image_url(img)
                if url and self._is_valid_image_url(url):
                    urls.add(url)
        
        # Strategy 3: Try main-image sections
        main_images = self.soup.select('.main-image img')
        for img in main_images:
            url = self._get_image_url(img)
            if url and self._is_valid_image_url(url):
                urls.add(url)
        
        # Strategy 4: Try source tags with srcset
        sources = self.soup.find_all('source')
        for source in sources:
            srcset = source.get('srcset')
            if srcset:
                url = srcset.split()[0] if ' ' in srcset else srcset
                if url and self._is_valid_image_url(url):
                    urls.add(url)
        
        return sorted(urls)  # Sort for consistent output
    
    @staticmethod
    def _is_valid_image_url(url: str) -> bool:
        """
        Check if image URL matches the required pattern and format.
        
        Pattern: https://img4.idealista.com/blur/WEB_DETAIL/0/id.pro.es.image.master/
        Format: .webp only
        
        Args:
            url: Image URL to validate
            
        Returns:
            True if URL matches criteria, False otherwise
        """
        if not url or url.startswith('data:'):
            return False
        
        # Check for WebP format
        if not url.lower().endswith('.webp'):
            return False
        
        # Check for required URL pattern
        required_pattern = 'https://img4.idealista.com/blur/WEB_DETAIL/0/id.pro.es.image.master/'
        if not url.startswith(required_pattern):
            return False
        
        return True
    
    @staticmethod
    def _get_image_url(img_tag) -> Optional[str]:
        """Extract URL from an img tag, trying multiple attributes."""
        return (img_tag.get('src') or 
                img_tag.get('data-src') or 
                img_tag.get('data-lazy-src') or
                img_tag.get('data-original'))


class BatchExtractor:
    """
    Batch extractor for processing multiple HTML files.
    
    Processes all .html files in a directory (including subdirectories)
    and outputs results to a JSON file.
    """
    
    def __init__(self, source_dir: str = "source_html", output_file: str = "parsed_properties.json"):
        """
        Initialize batch extractor.
        
        Args:
            source_dir: Directory containing HTML files (default: "source_html")
            output_file: Output JSON file path (default: "parsed_properties.json")
        """
        self.source_dir = Path(source_dir)
        self.output_file = Path(output_file)
        self.results: List[Dict] = []
        self.errors: List[Dict] = []
    
    def find_html_files(self) -> List[Path]:
        """
        Find all .html files in source directory recursively.
        
        Returns:
            List of Path objects for HTML files
        """
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")
        
        # Recursively find all .html files
        html_files = list(self.source_dir.rglob("*.html"))
        return sorted(html_files)
    
    def process_file(self, html_file: Path) -> Optional[Dict]:
        """
        Process a single HTML file.
        
        Args:
            html_file: Path to HTML file
            
        Returns:
            Dictionary with extracted data or None if error
        """
        try:
            extractor = PropertyExtractor(str(html_file))
            data = extractor.extract()
            
            # Add metadata
            result = data.to_dict()
            result['source_file'] = str(html_file.relative_to(self.source_dir))
            
            return result
        
        except Exception as e:
            error_info = {
                'file': str(html_file.relative_to(self.source_dir)),
                'error': str(e),
                'error_type': type(e).__name__
            }
            self.errors.append(error_info)
            return None
    
    def process_all(self, verbose: bool = True) -> Dict:
        """
        Process all HTML files in source directory.
        
        Args:
            verbose: Print progress messages
            
        Returns:
            Dictionary with results and statistics
        """
        html_files = self.find_html_files()
        
        if verbose:
            print(f"Found {len(html_files)} HTML files in {self.source_dir}")
            print("=" * 60)
        
        self.results = []
        self.errors = []
        
        for i, html_file in enumerate(html_files, 1):
            if verbose:
                print(f"[{i}/{len(html_files)}] Processing: {html_file.name}...", end=" ")
            
            result = self.process_file(html_file)
            
            if result:
                self.results.append(result)
                if verbose:
                    print("✓")
            else:
                if verbose:
                    print("✗")
        
        if verbose:
            print("=" * 60)
            print(f"Completed: {len(self.results)} successful, {len(self.errors)} errors")
        
        return {
            'total_files': len(html_files),
            'successful': len(self.results),
            'errors': len(self.errors)
        }
    
    def save_results(self, verbose: bool = True) -> None:
        """
        Save results to JSON file.
        
        Args:
            verbose: Print status message
        """
        output_data = {
            'properties': self.results,
            'metadata': {
                'total_properties': len(self.results),
                'extraction_errors': len(self.errors),
                'errors': self.errors
            }
        }
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        if verbose:
            print(f"\n✓ Results saved to: {self.output_file}")
            print(f"  - {len(self.results)} properties extracted")
            if self.errors:
                print(f"  - {len(self.errors)} errors (see metadata.errors in JSON)")
    
    def run(self, verbose: bool = True) -> None:
        """
        Run the complete batch extraction process.
        
        Args:
            verbose: Print progress messages
        """
        try:
            stats = self.process_all(verbose=verbose)
            self.save_results(verbose=verbose)
        except Exception as e:
            print(f"Fatal error: {e}")
            raise


class PropertyFormatter:
    """Formats property data for output."""
    
    @staticmethod
    def pretty_print(data: PropertyData) -> str:
        """
        Format property data for pretty printing.
        
        Args:
            data: PropertyData object
            
        Returns:
            Formatted string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("PROPERTY DATA EXTRACTION")
        lines.append("=" * 60)
        
        lines.append(f"\nTitle: {data.title}")
        lines.append(f"Operation: {data.operation_type or 'Unknown'}")
        lines.append(f"Property Type: {data.property_type or 'Unknown'}")
        lines.append(f"Price: {data.price}")
        
        if data.location:
            lines.append(f"\nLocation:")
            for key, value in data.location.items():
                lines.append(f"  {key.capitalize()}: {value}")
        
        lines.append(f"\nFeatures ({len(data.features)}):")
        for i, feature in enumerate(data.features, 1):
            lines.append(f"  {i}. {feature}")
        
        lines.append(f"\nDescription:")
        lines.append(f"  {data.description}")
        
        lines.append(f"\nImages ({len(data.images)}):")
        for i, url in enumerate(data.images, 1):
            lines.append(f"  {i}. {url}")
        
        lines.append("=" * 60)
        
        return '\n'.join(lines)


def main():
    """Main function to run the extractor from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract property data from Idealista HTML files')
    parser.add_argument('path', nargs='?', help='Path to HTML file or directory (for batch mode)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--batch', action='store_true', help='Batch process all HTML files in directory')
    parser.add_argument('--source-dir', default='source_html', help='Source directory for batch mode (default: source_html)')
    parser.add_argument('--output', default='parsed_properties.json', help='Output file for batch mode (default: parsed_properties.json)')
    parser.add_argument('--quiet', action='store_true', help='Suppress progress messages in batch mode')
    
    args = parser.parse_args()
    
    # Batch mode
    if args.batch:
        try:
            batch = BatchExtractor(
                source_dir=args.source_dir,
                output_file=args.output
            )
            batch.run(verbose=not args.quiet)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error during batch processing: {e}")
            sys.exit(1)
        return
    
    # Single file mode
    if not args.path:
        parser.print_help()
        sys.exit(1)
    
    html_path = args.path
    output_json = args.json
    
    try:
        # Create extractor and extract data
        extractor = PropertyExtractor(html_path)
        data = extractor.extract()
        
        if output_json:
            # Output as JSON
            print(data.to_json())
        else:
            # Pretty print
            formatter = PropertyFormatter()
            print(formatter.pretty_print(data))
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error extracting data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()