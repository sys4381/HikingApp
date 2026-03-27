from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from database import get_db, engine, Base
from models import Trail, TrailGroup
from ingest import process_directory

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Hiking App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class IngestRequest(BaseModel):
    directory_path: str

@app.post("/api/ingest")
def trigger_ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger the ingestion of a GPX directory."""
    import os
    if not os.path.isdir(request.directory_path):
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    # Run in background to not block the request
    background_tasks.add_task(process_directory, request.directory_path)
    return {"message": f"Started ingestion of {request.directory_path} in the background."}

@app.get("/api/groups")
def get_groups(directory: str = None, db: Session = Depends(get_db)):
    """Return all trail groups."""
    groups = db.query(TrailGroup).all()
    # attach counts
    result = []
    for g in groups:
        if directory:
            dir_filter = f"{directory}%"
            trail_count = db.query(Trail).filter(Trail.group_id == g.id, Trail.file_path.like(dir_filter)).count()
        else:
            trail_count = db.query(Trail).filter(Trail.group_id == g.id).count()
            
        if trail_count > 0:
            result.append({
                "id": g.id,
                "center_lat": g.center_lat,
                "center_lon": g.center_lon,
                "radius_km": g.radius_km,
                "trail_count": trail_count
            })
    return result

@app.get("/api/groups/{group_id}/trails")
def get_trails_in_group(group_id: int, directory: str = None, db: Session = Depends(get_db)):
    """Return all trails in a specific group."""
    group = db.query(TrailGroup).filter(TrailGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
        
    query = db.query(Trail).filter(Trail.group_id == group_id)
    if directory:
        dir_filter = f"{directory}%"
        query = query.filter(Trail.file_path.like(dir_filter))
        
    trails = query.all()
    return trails

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
