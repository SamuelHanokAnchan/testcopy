# image-resource-planner

``
pip install -r requirements.txt
``
``
sh startup.sh
``

## Software Split
Frontend: 
* Area selection (points on the picture)
* send pictureId with points to backend
* Select Layers and switch materials
 
Backend: 
* Load picture from db/storage
* Perform area calculation
  * Either based on multiple point selection for custom area
  * OR use SAM for auto-detection based on click.
* Return Area, size and Material list
* (optional) Detect type of Area and create probably required layers


## Routes
* GET /angleData: Get angle data from a specified image
* GET /area/custom: get the area information from the selected points
* GET /area/smart: get the area information auto detected from the selected point

## Backend-Components
* Model Loader -> Loads the SAM models, abstraction to enable load from file, url or external storage.
* Image Service -> Loads images based on an idea. Also layer of abstraction to enable different image sources
