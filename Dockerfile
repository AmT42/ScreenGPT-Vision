FROM python:3.8-slim

# Set the working directory in the container to match the Dockerfile location
WORKDIR /backend

# Copy the current directory contents into the container at /usr/src/app
COPY ./app /backend/app
COPY requirements.txt /backend/

RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches 
# host 0,0,0,0 This tells Uvicorn to listen on all network interfaces inside the Docker container. is a special value that makes your server accessible to external requests, not just ones from inside the container.
# --port 8000 This specifies the port on which Uvicorn will run your FastAPI application inside the Docker container.
CMD ["uvicorn","app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 