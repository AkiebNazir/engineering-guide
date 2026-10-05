from fastapi import FastAPI, File, UploadFile
import uvicorn

app = FastAPI()

@app.post("/upload")
async def upload_file(profile_pic: UploadFile = File(...)):
    # Read first 100 bytes just to verify
    contents = await profile_pic.read(100)
    print(f"File contents read: {len(contents)} bytes")
    
    return {"filename": profile_pic.filename, "status": "Uploaded"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
