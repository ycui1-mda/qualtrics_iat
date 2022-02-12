from pathlib import Path
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# api_token = "iNKzBVNVAoTMhwnT2amhZRAP4dTBjkEVw9AbpRWg"
# brand_center = "mdanderson.co1"
# data_center = "iad1"
# headers = {"x-api-token": api_token}


class QualtricsTool:
    """Data model to manage Qualtrics-related tools
    Parameters:
    -----------
    api_token: str, the API token for the user
    data_center: str, the data center for the user
    brand_center: str, the brand center for the user
        """
    def __init__(self, api_token=None, data_center=None, brand_center=None):
        self.api_token = api_token
        self.data_center = data_center
        self.brand_center = brand_center

    @property
    def api_headers(self):
        """The default API headers"""
        return {"x-api-token": self.api_token}
    
    @property
    def base_url(self):
        """The default base URL"""
        return f"https://{self.data_center}.qualtrics.com"
    
    @property
    def api_base_url(self):
        """The default base API URL"""
        return f"{self.base_url}/API/v3"
    
    def upload_images_api(self,
                          local_image_folder,
                          library_id,
                          creating_full_url=True,
                          qualtrics_folder=None,
                          filename_pattern="*"):
        """Upload images from the local folder to the Qualtrics server
        :param local_image_folder: str, Path, the local folder containing the images
        :param library_id: str, Qualtrics library ID number
        :param creating_full_url: bool, whether returns the IDs only or the full URLs
        :param qualtrics_folder: str, the Qualtrics Graphics folder for the uploaded images
        :param filename_pattern: str, the pattern using which to select the images for uploading
        :return list[str], the list of image IDs or URLs
        """
        upload_url = f"{self.api_base_url}/libraries/{library_id}/graphics"
        image_urls = list()
        for file in Path(local_image_folder).glob(filename_pattern):
            file_type = Path(file)[1:]
            if file_type not in ("png", "gif", "jpg", "jpeg"):
                raise ValueError("Qualtrics only accepts PNG, GIF, and JPEG images.")
            encoded_fields = {'file': (file.name, open(file, 'rb'), f'image/{file_type}')}
            image_url_id = self._upload_image(encoded_fields, qualtrics_folder, upload_url, file, creating_full_url)
            image_urls.append(image_url_id)
        return image_urls
    
    def upload_images_web(self,
                          image_files,
                          library_id,
                          creating_full_url,
                          qualtrics_folder,
                          image_type):
        """Upload images from the web app to the Qualtrics server
        :param image_files: Bytes, the uploaded bytes data from the web app
        :param library_id: str, Qualtrics library ID number
        :param creating_full_url: bool, whether returns the IDs only or the full URLs
        :param qualtrics_folder: str, the Qualtrics Graphics folder for the uploaded images
        :param image_type: str, the image file type
        :return list[str], the list of image IDs or URLs
        """
        image_urls = list()
        upload_url = f"{self.api_base_url}/libraries/{library_id}/graphics"
        file_count_digit = len(str(len(image_files)))
        for file_i, file in enumerate(image_files, start=1):
            encoded_fields = {'file': (f"image{file_i:0>{file_count_digit}}.{image_type}", file, f'image/{image_type}')}
            image_url_id = self._upload_image(encoded_fields, qualtrics_folder, upload_url, file, creating_full_url)
            image_urls.append(image_url_id)
        return image_urls
    
    def _upload_image(self, encoded_fields, qualtrics_folder, upload_url, file, creating_full_url):
        if qualtrics_folder:
            encoded_fields['folder'] = qualtrics_folder
        mp_encoder = MultipartEncoder(fields=encoded_fields)
        post_request = requests.post(
            upload_url,
            data=mp_encoder,
            headers={'Content-Type': mp_encoder.content_type, **self.api_headers}
        )
        try:
            image_url_id = post_request.json()['result']['id']
        except KeyError:
            raise Exception(f"Failed to upload image {file.name}")
        if creating_full_url:
            image_url_id = f"{self.base_url}/ControlPanel/Graphic.php?IM={image_url_id}"
        return image_url_id
    
    def delete_images(self, library_id, image_url_ids):
        """Delete images from the specified library
        :param library_id: str, the library ID number
        :param image_url_ids: list[str], the image IDs or full URLs
        :return dict, the deletion report"""
        report = dict()
        for image_url_id in image_url_ids:
            if image_url_id.find("=") > 0:
                image_url_id = image_url_id[image_url_id.index("=") + 1:]
            url = f'{self.api_base_url}/libraries/{library_id}/graphics/{image_url_id}'
            delete_response = requests.delete(url, headers=self.api_headers)
            try:
                http_status = delete_response.json()['meta']['httpStatus']
            except KeyError:
                raise Exception(f"Failed to delete image: {image_url_id}")
            else:
                report[image_url_id] = "Deleted" if http_status.startswith('200') else "Error"
        return report
    
    def create_survey(self, template_json):
        """Create the survey using the JSON template
        :param template_json: str in the JSON format, the JSON file for the qsf file
        :return str, the created Survey ID number
        """
        upload_url = f"{self.api_base_url}/survey-definitions"
        creation_response = requests.post(
            upload_url,
            json=template_json,
            headers={**self.api_headers, "content-type": "application/json"}
        )
        try:
            survey_id = creation_response.json()['result']['SurveyID']
        except KeyError:
            raise Exception("Couldn't create the survey. Please check the params.")
        
        return survey_id
    
    def delete_survey(self, survey_id):
        """Delete the survey
        :param survey_id: str, the survey ID number
        :return dict, the deletion report
        """
        report = dict()
        delete_url = f"{self.api_base_url}/survey-definitions/{survey_id}"
        delete_response = requests.delete(delete_url, headers=self.api_headers)
        try:
            http_status = delete_response.json()['meta']['httpStatus']
        except KeyError:
            raise Exception(f"Failed to delete survey: {survey_id}")
        else:
            report[survey_id] = "Deleted" if http_status.startswith('200') else "Error"
        return report
    
    def export_responses(self, survey_id, file_format="csv", data_folder=None):
        """Export responses from the Qualtrics survey"""
        download_url = f"{self.api_base_url}/surveys/{survey_id}/export-responses/"
        download_payload = f'{{"format": "{file_format}"}}'
        download_response = requests.post(
            download_url,
            data=download_payload,
            headers={**self.api_headers, "content-type": "application/json"}
        )
        try:
            progress_id = download_response.json()["result"]["progressId"]
            file_id = self._monitor_progress(download_url, progress_id)
            file_content = self._download_file(download_url, file_id)
        except KeyError:
            raise Exception("Can't download the responses. Please check the params.")
        return file_content
    
    def _monitor_progress(self, download_url, progress_id):
        progress_status = "inProgress"
        while progress_status != "complete" and progress_status != "failed":
            progress_response = requests.get(download_url + progress_id, headers=self.api_headers)
            progress_status = progress_response.json()["result"]["status"]
        return progress_response.json()["result"]["fileId"]
    
    def _download_file(self, download_url, file_id):
        file_url = f"{download_url}/{file_id}/file"
        file_response = requests.get(file_url, headers=self.api_headers, stream=True)
        return file_response.content
