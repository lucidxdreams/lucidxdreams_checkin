#!/usr/bin/env python3
"""
Script to retrieve field metadata from QuickBase table
Usage: python get_quickbase_fields.py
"""

import requests
import json
import sys
from typing import Dict, List

# Configuration
QB_REALM = "octo.quickbase.com"
QB_TABLE_ID = "bscn22va8"
QB_TOKEN = "cbjkgg_rzbr_0_586zzwbrq9qsccjm4zj9ct5u46w"

class QuickBaseFieldAnalyzer:
    def __init__(self, token: str, realm: str, table_id: str):
        self.base_url = "https://api.quickbase.com/v1"
        self.realm = realm
        self.table_id = table_id
        self.headers = {
            "QB-Realm-Hostname": realm,
            "Authorization": f"QB-USER-TOKEN {token}",
            "Content-Type": "application/json",
            "User-Agent": "MedicalCardFieldAnalyzer/1.0"
        }
    
    def get_fields(self) -> List[Dict]:
        """Retrieve all fields from the table"""
        url = f"{self.base_url}/fields"
        params = {"tableId": self.table_id}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"❌ Error: {e}")
            print(f"Response: {response.text}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            sys.exit(1)
    
    def categorize_fields(self, fields: List[Dict]) -> Dict:
        """Categorize fields by type and purpose"""
        categorized = {
            "system_fields": [],      # Record ID, Date Created, etc.
            "text_fields": [],         # Name, address, etc.
            "contact_fields": [],      # Email, phone
            "date_fields": [],         # DOB, dates
            "file_fields": [],         # ID attachments
            "choice_fields": [],       # Dropdowns, multi-choice
            "other_fields": []
        }
        
        for field in fields:
            field_info = {
                "id": field["id"],
                "label": field["label"],
                "type": field["fieldType"],
                "required": field.get("required", False),
                "unique": field.get("unique", False)
            }
            
            field_type = field["fieldType"]
            field_label = field["label"].lower()
            
            # System fields (usually ID 1-5)
            if field["id"] <= 5 or field_type in ["recordid", "timestamp"]:
                categorized["system_fields"].append(field_info)
            
            # File attachments
            elif field_type == "file":
                categorized["file_fields"].append(field_info)
            
            # Contact information
            elif field_type in ["email", "phone"] or any(x in field_label for x in ["email", "phone", "contact"]):
                categorized["contact_fields"].append(field_info)
            
            # Dates
            elif field_type in ["date", "datetime", "timestamp"]:
                categorized["date_fields"].append(field_info)
            
            # Choice fields
            elif field_type in ["text-multiple-choice", "checkbox", "rating"]:
                categorized["choice_fields"].append(field_info)
            
            # Text fields
            elif field_type in ["text", "text-multi-line", "rich-text"]:
                categorized["text_fields"].append(field_info)
            
            # Everything else
            else:
                categorized["other_fields"].append(field_info)
        
        return categorized
    
    def print_analysis(self, fields: List[Dict]):
        """Print formatted field analysis"""
        print("\n" + "="*80)
        print(f"QUICKBASE TABLE FIELD ANALYSIS: {self.table_id}")
        print("="*80 + "\n")
        
        categorized = self.categorize_fields(fields)
        
        # Print summary
        print("📊 SUMMARY")
        print("-" * 80)
        print(f"Total Fields: {len(fields)}")
        print(f"  • System Fields: {len(categorized['system_fields'])}")
        print(f"  • Text Fields: {len(categorized['text_fields'])}")
        print(f"  • Contact Fields: {len(categorized['contact_fields'])}")
        print(f"  • Date Fields: {len(categorized['date_fields'])}")
        print(f"  • File Fields: {len(categorized['file_fields'])}")
        print(f"  • Choice Fields: {len(categorized['choice_fields'])}")
        print(f"  • Other Fields: {len(categorized['other_fields'])}")
        print()
        
        # Required fields
        required_fields = [f for f in fields if f.get("required", False)]
        print(f"⚠️  REQUIRED FIELDS: {len(required_fields)}")
        print("-" * 80)
        for field in required_fields:
            print(f"  [ID {field['id']:3}] {field['label']} ({field['fieldType']})")
        print()
        
        # Print each category
        self._print_category("📝 TEXT FIELDS", categorized["text_fields"])
        self._print_category("📞 CONTACT FIELDS", categorized["contact_fields"])
        self._print_category("📅 DATE FIELDS", categorized["date_fields"])
        self._print_category("📎 FILE FIELDS", categorized["file_fields"])
        self._print_category("☑️  CHOICE FIELDS", categorized["choice_fields"])
        self._print_category("🔧 SYSTEM FIELDS", categorized["system_fields"])
        
        if categorized["other_fields"]:
            self._print_category("❓ OTHER FIELDS", categorized["other_fields"])
        
        print("\n" + "="*80)
        print("FIELD MAPPING FOR CODE")
        print("="*80)
        print("\nCopy this into your quickbase_api.py:\n")
        print("FIELD_IDS = {")
        
        # Generate mapping based on likely matches
        for field in fields:
            label = field["label"]
            field_id = field["id"]
            field_type = field["fieldType"]
            
            # Skip system fields
            if field_id <= 5:
                continue
            
            # Create Python-friendly key
            key = label.upper().replace(" ", "_").replace("-", "_")
            required = " # REQUIRED" if field.get("required") else ""
            print(f'    "{key}": {field_id},  # {label} ({field_type}){required}')
        
        print("}\n")
    
    def _print_category(self, title: str, fields: List[Dict]):
        """Print a category of fields"""
        if not fields:
            return
        
        print(f"{title}: {len(fields)}")
        print("-" * 80)
        for field in fields:
            required_badge = " [REQUIRED]" if field["required"] else ""
            unique_badge = " [UNIQUE]" if field["unique"] else ""
            print(f"  [ID {field['id']:3}] {field['label']}{required_badge}{unique_badge}")
            print(f"           Type: {field['type']}")
        print()
    
    def export_json(self, fields: List[Dict], filename: str = "quickbase_fields.json"):
        """Export field data to JSON"""
        with open(filename, "w") as f:
            json.dump(fields, f, indent=2)
        print(f"✅ Field data exported to: {filename}")

def main():
    print("\n🔍 QuickBase Field Analyzer")
    print("=" * 80)
    
    analyzer = QuickBaseFieldAnalyzer(QB_TOKEN, QB_REALM, QB_TABLE_ID)
    
    print(f"\n📡 Fetching fields from table '{QB_TABLE_ID}'...")
    fields = analyzer.get_fields()
    
    # Print analysis
    analyzer.print_analysis(fields)
    
    # Export to JSON
    output_file = f"../docs/quickbase_fields_{QB_TABLE_ID}.json"
    analyzer.export_json(fields, output_file)
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("1. Review the field mapping above")
    print("2. Identify which fields need OCR extraction vs. user input")
    print("3. Update backend/quickbase_api.py with correct field IDs")
    print("4. Test with a sample submission\n")

if __name__ == "__main__":
    main()
