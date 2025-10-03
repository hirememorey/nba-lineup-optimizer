# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements files into the container at /app
COPY requirements.txt requirements_streamlit.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements_streamlit.txt

# Copy the entire project directory into the container
COPY . .

# Command to run the training script
# This will be executed when the container launches
CMD ["python", "train_bayesian_model.py"]
