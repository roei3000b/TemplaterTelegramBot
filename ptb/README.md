# Templater API

A Flask API to fill DOCX/PPTX templates with city-specific data.

## Requirements

- Docker

## Build and Run with Docker

1. Build the image:  
   docker build -t templater-app .

2. Run the server:  
   docker run -p 5000:5000 templater-app

The API will be available at http://localhost:5000

## API Usage

POST /fill-template  
Form fields:
- city: city name (e.g., חריש)
- file: DOCX or PPTX template

Returns:
- On success: filled file as attachment (UTF-8 filename supported)
- On error: JSON error

## Example Client

Run the example script:

python fill_template_request_example.py

This sends a request and saves the filled file using the server's filename (UTF-8 safe).