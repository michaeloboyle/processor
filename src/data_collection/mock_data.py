"""
Mock data generator for property tax appeals demonstration
Based on typical Pennsylvania property assessment patterns
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.data_collection.models import PropertyRecord, AppealRecord


class LackawannaMockDataGenerator:
    """Generate realistic mock data for Lackawanna County property tax appeals"""
    
    def __init__(self):
        self.street_names = [
            "Main St", "Oak Ave", "Pine St", "Church St", "Washington Ave",
            "Jefferson St", "Lincoln Ave", "Madison St", "Adams Ave", "Monroe St",
            "Elm St", "Maple Ave", "Cedar St", "Spruce Ave", "Walnut St",
            "1st Street", "2nd Street", "3rd Street", "Market St", "State St",
            "Pennsylvania Ave", "Mulberry St", "Vine St", "North St", "South St"
        ]
        
        self.property_types = [
            "Residential", "Commercial", "Industrial", "Vacant Land", 
            "Apartment Building", "Mixed Use", "Institutional"
        ]
        
        self.appeal_reasons = [
            "Overassessment", "Incorrect Property Information", "Uniformity Issues",
            "Market Value Dispute", "Clerical Error", "Property Condition",
            "Comparable Sales Analysis", "Hardship"
        ]
        
        self.owner_names = [
            "John Smith", "Mary Johnson", "Robert Williams", "Patricia Brown",
            "Michael Davis", "Linda Miller", "David Wilson", "Susan Moore",
            "James Taylor", "Barbara Anderson", "Richard Thomas", "Nancy Jackson",
            "Joseph White", "Carol Harris", "Thomas Martin", "Sarah Thompson"
        ]
        
        # Assessment ratios typical for PA counties (80-100% of market value)
        self.assessment_ratios = [0.75, 0.80, 0.85, 0.90, 0.95, 1.0, 1.05, 1.10]
        
    def generate_property_records(self, count: int = 100) -> List[PropertyRecord]:
        """Generate realistic property records"""
        properties = []
        
        for i in range(count):
            # Generate address
            house_number = random.randint(100, 9999)
            street = random.choice(self.street_names)
            address = f"{house_number} {street}, Scranton, PA"
            
            # Generate property ID (typical format: parcel-block-lot)
            parcel = random.randint(10, 99)
            block = random.randint(100, 999)
            lot = random.randint(10, 99)
            property_id = f"{parcel}-{block}-{lot}"
            
            # Generate market value (realistic for Scranton area)
            property_type = random.choice(self.property_types)
            if property_type == "Residential":
                market_value = random.randint(50000, 300000)
            elif property_type == "Commercial":
                market_value = random.randint(150000, 1500000)
            elif property_type == "Industrial":
                market_value = random.randint(200000, 2000000)
            elif property_type == "Apartment Building":
                market_value = random.randint(300000, 1200000)
            else:
                market_value = random.randint(30000, 500000)
            
            # Generate assessed value with some variation
            assessment_ratio = random.choice(self.assessment_ratios)
            assessed_value = int(market_value * assessment_ratio)
            
            # Round to nearest $1000 for realism
            assessed_value = round(assessed_value / 1000) * 1000
            market_value = round(market_value / 1000) * 1000
            
            property_record = PropertyRecord(
                property_id=property_id,
                address=address,
                assessed_value=assessed_value,
                market_value=market_value,
                owner_name=random.choice(self.owner_names),
                property_type=property_type,
                last_updated=datetime.utcnow() - timedelta(days=random.randint(30, 365))
            )
            
            properties.append(property_record)
        
        return properties
    
    def generate_appeal_records(self, property_records: List[PropertyRecord], 
                              appeal_rate: float = 0.15) -> List[AppealRecord]:
        """Generate realistic appeal records for properties"""
        appeals = []
        
        # Select properties that will have appeals (typically 10-20% of properties)
        num_appeals = int(len(property_records) * appeal_rate)
        appealing_properties = random.sample(property_records, num_appeals)
        
        for i, property_record in enumerate(appealing_properties):
            # Generate appeal ID
            year = 2024
            appeal_id = f"AP-{year}-{i+1:03d}"
            
            # Appeal date (within last 12 months)
            appeal_date = datetime.utcnow() - timedelta(days=random.randint(30, 365))
            
            # Determine appeal reason (overassessment is most common)
            reason_weights = {
                "Overassessment": 0.4,
                "Market Value Dispute": 0.2,
                "Comparable Sales Analysis": 0.15,
                "Property Condition": 0.1,
                "Incorrect Property Information": 0.08,
                "Uniformity Issues": 0.05,
                "Clerical Error": 0.02
            }
            
            reason = random.choices(
                list(reason_weights.keys()),
                weights=list(reason_weights.values())
            )[0]
            
            # Generate requested value (typically 10-30% reduction)
            if reason in ["Overassessment", "Market Value Dispute", "Comparable Sales Analysis"]:
                reduction_percent = random.uniform(0.10, 0.30)
            elif reason in ["Property Condition", "Uniformity Issues"]:
                reduction_percent = random.uniform(0.15, 0.35)
            else:
                reduction_percent = random.uniform(0.05, 0.20)
            
            requested_value = int(property_record.assessed_value * (1 - reduction_percent))
            requested_value = round(requested_value / 1000) * 1000  # Round to nearest $1000
            
            # Determine status (mix of pending, approved, denied)
            status_weights = {"Pending": 0.6, "Under Review": 0.2, "Scheduled": 0.15, "Resolved": 0.05}
            status = random.choices(
                list(status_weights.keys()),
                weights=list(status_weights.values())
            )[0]
            
            # Generate hearing date if scheduled
            hearing_date = None
            if status in ["Scheduled", "Under Review"]:
                hearing_date = (datetime.utcnow() + timedelta(days=random.randint(30, 90))).strftime("%Y-%m-%d")
            
            # Generate resolution for resolved cases
            resolution = None
            final_value = None
            if status == "Resolved":
                outcomes = ["Approved - Full Reduction", "Approved - Partial Reduction", "Denied"]
                outcome_weights = [0.25, 0.45, 0.30]
                resolution = random.choices(outcomes, weights=outcome_weights)[0]
                
                if "Approved" in resolution:
                    if "Full" in resolution:
                        final_value = requested_value
                    else:  # Partial reduction
                        partial_reduction = random.uniform(0.3, 0.7)
                        reduction_amount = property_record.assessed_value - requested_value
                        final_value = property_record.assessed_value - int(reduction_amount * partial_reduction)
                        final_value = round(final_value / 1000) * 1000
                else:  # Denied
                    final_value = property_record.assessed_value
            
            appeal_record = AppealRecord(
                appeal_id=appeal_id,
                property_id=property_record.property_id,
                appeal_date=appeal_date.strftime("%Y-%m-%d"),
                status=status,
                requested_value=requested_value,
                reason=reason,
                hearing_date=hearing_date,
                resolution=resolution,
                final_value=final_value
            )
            
            appeals.append(appeal_record)
        
        return appeals
    
    def generate_sample_dataset(self, num_properties: int = 100) -> Dict[str, Any]:
        """Generate a complete sample dataset"""
        print(f"Generating {num_properties} properties with realistic appeal patterns...")
        
        # Generate properties
        properties = self.generate_property_records(num_properties)
        
        # Generate appeals (typically 10-20% of properties have appeals)
        appeals = self.generate_appeal_records(properties, appeal_rate=0.15)
        
        # Generate statistics
        total_assessed_value = sum(p.assessed_value for p in properties)
        total_market_value = sum(p.market_value for p in properties)
        pending_appeals = len([a for a in appeals if a.status == "Pending"])
        total_appeal_value = sum(a.requested_value for a in appeals)
        
        dataset = {
            "properties": properties,
            "appeals": appeals,
            "statistics": {
                "total_properties": len(properties),
                "total_appeals": len(appeals),
                "appeal_rate": len(appeals) / len(properties),
                "total_assessed_value": total_assessed_value,
                "total_market_value": total_market_value,
                "average_assessed_value": total_assessed_value // len(properties),
                "pending_appeals": pending_appeals,
                "total_requested_reduction": sum(
                    p.assessed_value - a.requested_value 
                    for p in properties 
                    for a in appeals 
                    if a.property_id == p.property_id
                ),
                "generation_timestamp": datetime.utcnow().isoformat()
            }
        }
        
        print(f"Generated dataset:")
        print(f"  - {len(properties)} properties")
        print(f"  - {len(appeals)} appeals ({len(appeals)/len(properties)*100:.1f}% appeal rate)")
        print(f"  - {pending_appeals} pending appeals")
        print(f"  - ${total_assessed_value:,} total assessed value")
        print(f"  - ${dataset['statistics']['total_requested_reduction']:,} total requested reduction")
        
        return dataset


def generate_lackawanna_demo_data():
    """Generate demo data for Lackawanna County"""
    generator = LackawannaMockDataGenerator()
    return generator.generate_sample_dataset(num_properties=50)


if __name__ == "__main__":
    # Generate and save demo data
    import json
    import os
    
    demo_data = generate_lackawanna_demo_data()
    
    # Create demo data directory
    os.makedirs("demo_data", exist_ok=True)
    
    # Save as JSON (converting Pydantic models to dicts)
    json_data = {
        "properties": [p.model_dump() for p in demo_data["properties"]],
        "appeals": [a.model_dump() for a in demo_data["appeals"]],
        "statistics": demo_data["statistics"]
    }
    
    with open("demo_data/lackawanna_demo_dataset.json", "w") as f:
        json.dump(json_data, f, indent=2, default=str)
    
    print("\nDemo data saved to: demo_data/lackawanna_demo_dataset.json")