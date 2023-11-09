from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()


@app.post("/upload_screenshot")
async def upload_screenshot(file: UploadFile = File(...)):
    # Save the screenshot to a file
    with open("storage/screenshot.png", "wb") as buffer:
        buffer.write(file.file.read())

    return JSONResponse(content={"message": "Screen shot received successfully"}, status_code=200)