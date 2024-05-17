from fastapi import FastAPI, HTTPException
from typing import List
from PIL import Image
from PIL.ExifTags import TAGS
import piexif
import os

app = FastAPI()


class ImageSearchEngine:
    def __init__(self):
        self.image_data = {}

    def add_image(self, image_path):
        image = Image.open(image_path)
        exifdata = image._getexif()
        tags = []
        for tag_id in exifdata:
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'ImageDescription':
                data = exifdata.get(tag_id)
                if isinstance(data, bytes):
                    tags = data.decode().split(',')
        print(tags)
        self.image_data[image_path] = tags

    def search_images(self, query):
        result_images = []
        for image_path, tags in self.image_data.items():
            if query in tags:
                result_images.append({'path': image_path, 'tags': tags})
        return result_images

    def add_tag(self, image_path, tag):
        if image_path in self.image_data:
            self.image_data[image_path].append(tag)
            exif_dict = piexif.load(image_path)
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = ','.join(
                self.image_data[image_path])
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_path)
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    def remove_tag(self, image_path, tag):
        if image_path in self.image_data and tag in self.image_data[image_path]:
            self.image_data[image_path].remove(tag)
            exif_dict = piexif.load(image_path)
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = ','.join(
                self.image_data[image_path])
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_path)
        else:
            raise HTTPException(
                status_code=404, detail="Image or tag not found")

    def update_tags(self, image_path, new_tags):
        if image_path in self.image_data:
            self.image_data[image_path] = new_tags
            exif_dict = piexif.load(image_path)
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = ','.join(
                new_tags)
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_path)
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    def delete_image(self, image_path):
        if image_path in self.image_data:
            del self.image_data[image_path]
            exif_dict = piexif.load(image_path)
            exif_dict['0th'][piexif.ImageIFD.ImageDescription] = ''
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, image_path)
        else:
            raise HTTPException(status_code=404, detail="Image not found")


search_engine = ImageSearchEngine()


@app.on_event("startup")
async def startup_event():
    for root, dirs, files in os.walk('static/images'):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):
                search_engine.add_image(os.path.join(root, file))


@app.get("/search/{query}")
async def search_images(query: str):
    return search_engine.search_images(query)


@app.post("/add_tag/{image_path}/{tag}")
async def add_tag(image_path: str, tag: str):
    search_engine.add_tag(image_path, tag)
    return {"message": "Tag added successfully"}


@app.delete("/remove_tag/{image_path}/{tag}")
async def remove_tag(image_path: str, tag: str):
    search_engine.remove_tag(image_path, tag)
    return {"message": "Tag removed successfully"}


@app.delete("/delete_image/{image_path}")
async def delete_image(image_path: str):
    search_engine.delete_image(image_path)
    return {"message": "Image deleted successfully"}


@app.put("/update_tags/{image_path}")
async def update_tags(image_path: str, tags: List[str]):
    search_engine.update_tags(image_path, tags)
    return {"message": "Tags updated successfully"}
