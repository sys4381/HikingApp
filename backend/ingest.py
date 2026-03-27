import os
import sys
import argparse
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Trail, TrailGroup
from parser import extract_gpx_data
import geopy.distance

Base.metadata.create_all(bind=engine)

def get_or_create_group(db: Session, lat: float, lon: float, radius_km: float = 10.0) -> TrailGroup:
    # Find existing groups
    groups = db.query(TrailGroup).all()
    for group in groups:
        dist = geopy.distance.geodesic((lat, lon), (group.center_lat, group.center_lon)).km
        if dist <= radius_km:
            return group
            
    # Create new group
    new_group = TrailGroup(center_lat=lat, center_lon=lon, radius_km=radius_km)
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    return new_group

def process_directory(directory: str):
    db: Session = SessionLocal()
    gpx_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.gpx'):
                gpx_files.append(os.path.join(root, file))
                
    print(f"Found {len(gpx_files)} GPX files.")
    
    for file_path in gpx_files:
        # Check if already processed
        existing = db.query(Trail).filter(Trail.file_path == file_path).first()
        if existing:
            print(f"Skipping {file_path}, already in DB.")
            continue
            
        print(f"Processing {file_path}...")
        data = extract_gpx_data(file_path)
        
        if "error" in data:
            print(f"Error processing {file_path}: {data['error']}")
            continue
            
        trail = Trail(**data)
        
        # Grouping
        group = get_or_create_group(db, trail.start_lat, trail.start_lon)
        trail.group_id = group.id
        
        db.add(trail)
        db.commit()
        print(f"Successfully added trail: {trail.name} (Group ID: {group.id})")

    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest GPX files into HikingApp DB")
    parser.add_argument("directory", help="Directory containing GPX files")
    args = parser.parse_args()
    
    process_directory(args.directory)
