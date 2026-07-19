# Sample File Access Service

## Overview

This is a small Flask service for managing access to research files

A user can download a file only when they have access to the sample and the file has passed QC

## How to Run

Install the dependencies

pip install -r requirements.txt

Start the app

python app.py

Run the tests

pytest

Run lint

flake8 app.py test_app.py

## Endpoints

POST /samples  
Creates a sample and adds files to it  
New files start with a QC status of pending

POST /samples/<sample_id>/grants  
Gives a user access to a sample

POST /files/<file_id>/qc  
Updates a file from pending to passed or failed

POST /download  
Checks the user's access and the file's QC status before returning a fake download URL

## Why I Built It This Way

I used Flask because the service is small and only needs a few endpoints, so I wanted to keep the implementation simple

I used in-memory storage because this is a time-boxed exercise and I wanted to focus more on the access and QC logic

I also check access before QC so a user without permission does not get information about the file's internal QC status

## Assumptions

Sample owners automatically have access to their own samples

Other users need to be granted access

The QC callback is coming from a trusted internal service

The download URL is only a fake example and expires after five minutes

## Things I Would Improve With More Time

The main limitation is that all data is lost when the app restarts
With more time, I would add a real database, authentication, better request validation, logging, signed download URLs, and a few more edge-case tests