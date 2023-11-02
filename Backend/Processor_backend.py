import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By  # Import the 'By' class for element locating
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import torch
import torchvision.transforms as T
from PIL import Image
import numpy as np
import cv2
import firebase_admin
from firebase_admin import credentials, storage, firestore

# Initialize Firebase with your JSON configuration file
cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'accio-2f266.appspot.com'  # Replace with your Firebase Storage bucket
})
# Reference to the Firebase Storage bucket
bucket = storage.bucket()
db= firestore.client()

options = webdriver.ChromeOptions()
prefs = {"download.default_directory": "D:\\3DModels"}
options.add_experimental_option("prefs", prefs)

# Load MiDaS Model
model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small").cuda().eval()

k = 0
# volume estimation and 3d model uploading image taking api
def find_volume(image, pixel_depth_short, pixel_depth_long, depth_nearest=2):
    # Load and Preprocess Input Image  # Replace with the path to your input image
    input_image = Image.open(image).convert("RGB")
    im = cv2.imread(image)

    # Image Preprocessing
    transform = T.Compose([
        T.Resize((384, 384)),  # Resize image to match the model's input size
        T.ToTensor(),  # Convert PIL image to PyTorch tensor
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize image
    ])
    input_tensor = transform(input_image).unsqueeze(0).cuda()  # Add batch dimension and move to GPU
    # Perform Depth Estimation
    with torch.no_grad():
        prediction = model(input_tensor)

    # Denormalize Depth Map
    depth_map_normalized = prediction.squeeze().cpu().numpy()
    depth_map_normalized = (depth_map_normalized - depth_map_normalized.min()) / (
            depth_map_normalized.max() - depth_map_normalized.min())
    depth_map_normalized = depth_nearest * (1 + depth_map_normalized)

    volume = np.sum(depth_map_normalized) * pixel_depth_short * pixel_depth_long * max(im.shape[0] / 384,
                                                                                       im.shape[1] / 384) - \
             im.shape[0] * im.shape[1] * (pixel_depth_short) * pixel_depth_long * depth_nearest
    return volume


def three_dimensional_model(image,location):
    download_path = os.path.join(os.getcwd(),f'models',f'{location}')
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": download_path}
    options.add_experimental_option("prefs", prefs)
    # example: prefs = {"download.default_directory" : "C:\Tutorial\down"};
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    os.makedirs(f"models", exist_ok=True)
    os.makedirs(f"models/{location}", exist_ok=True)
    driver.get("https://huggingface.co/spaces/shariqfarooq/ZoeDepth")
    driver.minimize_window()

    iframe = driver.find_element(By.TAG_NAME, 'iframe')
    driver.switch_to.frame(iframe)

    wait = WebDriverWait(driver, 30)
    try:
        element = wait.until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/gradio-app/div/div/div/div/div/div[3]/div[1]/button[2]')))
        element.click()
    except TimeoutException:
        print("Element not found or not clickable within the specified timeout.")

    time.sleep(10)

    # Find the file input element
    file_input = driver.find_element(By.XPATH,
                                     "/html/body/gradio-app/div/div/div/div/div/div[3]/div[3]/div/div[3]/div[1]/div["
                                     "3]/div/input")

    # Provide the correct file path for your image
    wait = WebDriverWait(driver, 30)
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                                            "/html/body/gradio-app/div/div/div/div/div/div[3]/div[3]/div/div[3]/div["
                                            "1]/div[3]/div/input"))
        )
        file_input.send_keys(image)
    except TimeoutException:
        print("Element not found or not clickable within the specified timeout.")

    time.sleep(10)

    # Find the checkbox element by name and type
    checkbox = driver.find_element(By.XPATH,
                                   "/html/body/gradio-app/div/div/div/div/div/div[3]/div[3]/div/div[4]/div/label/input")
    checkbox.click()
    time.sleep(10)

    # Find and click the submit button by its id
    submit = driver.find_element(By.XPATH, "/html/body/gradio-app/div/div/div/div/div/div[3]/div[3]/div/button")
    submit.click()
    time.sleep(10)
    # Find and click the download button
    wait = WebDriverWait(driver, 40)
    try:
        download = wait.until(EC.element_to_be_clickable((By.XPATH,
                                                          '/html/body/gradio-app/div/div/div/div/div/div[3]/div['
                                                          '3]/div/div[3]/div[2]/div[3]/div/a/button')))
        download.click()
    except TimeoutException:
        print("Element not found or not clickable within the specified timeout.")

    target_extension = '.glb'
    time.sleep(60)
    for filename in os.listdir(download_path):
        if filename.endswith(target_extension) and filename.startswith("_tmp"):
            global k
            # Found a file with the desired extension
            print(f"File found: {filename}")
            os.rename(os.path.join(download_path, filename), os.path.join(download_path, f'model{k}.glb'))
            k += 1
            # You can perform further actions on the file here
            driver.quit()
            return os.path.join(download_path, f'model{k}.glb')



class processer():
    def __int__(self):
        pass
    def run(self):
        while (True):
            # Path in Firebase Storage where you want to store the image
            # Path to the folder you want to check
            folder_path = "images"  # Replace with the actual folder path

            # List the contents of the folder
            blobs = list(bucket.list_blobs(prefix=folder_path))

            if not blobs:
                continue
            folder_path = "images"  # Replace with the actual folder path

            # List all the files in the folder
            blobs = bucket.list_blobs(prefix=folder_path)

            # Iterate through the list of blobs and print their names
            for blob in blobs:
                firebase_storage_path = blob.name
                image_path = "pot.jpg"

                # image pull and read
                blob = bucket.blob(firebase_storage_path)
                blob.download_to_filename(image_path)
                print(f"Image downloaded to local path: {image_path}")
                collection_name= "streamlocation"
                document_id = blob.name

                # doc_ref= db.collection("streamlocation").document(blob.name)
                # doc= doc_ref.get()
                #
                # if doc.exists:
                #     data= doc.to_dict()
                #     print(f"Document data: {data}")


                # Delete the image from Firebase Storage

                # image ka area
                depth_nearest = 2
                xp = depth_nearest * 2 * 0.279
                yp = depth_nearest * 2 * 0.689
                multiplicativeFactor_width = yp / int(1920 / 1.38)
                multiplicativeFactor_height = xp / int(1080 / 1.38)
                img = cv2.imread(image_path)
                area = multiplicativeFactor_height * img.shape[1] * multiplicativeFactor_width * img.shape[0]
                print("Area Done")
                # image ka location
                longitude, latitude = 21.249611, 81.606213

                location = f'{latitude} {longitude}'
                # image volume
                volume = find_volume(image_path, multiplicativeFactor_height, multiplicativeFactor_width, depth_nearest)
                print("Volume Done")
                # 3-dModel
                image_path = os.path.join(os.getcwd(),image_path)
                print(f"image_path {image_path}")
                model_path = three_dimensional_model(image_path,location)
                print("Model Done")
                print(area, volume)
                # file mai save kiya
                # data = {area, volume, longitude,latitude }
                data={"area": area, "volume": volume, "longitude": longitude, "latitude": latitude, "Model_path": model_path}
                db.collection('AfterProcess').document(location).set(data)

                os.remove(image_path)
                blob = bucket.blob(firebase_storage_path)
                blob.delete()
                print(f"Image deleted from Firebase Storage: {firebase_storage_path}")
                # firebase upload

process = processer()  # Processing backend
process.run()